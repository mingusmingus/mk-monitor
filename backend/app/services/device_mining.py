"""
Device Mining Service.

Responsible for connecting to Mikrotik devices and mining deep forensic data.
Handles version differences (v6 vs v7), error handling, and data structuring.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

# Attempt to import routeros_api, handle missing dependency gracefully
try:
    from routeros_api import RouterOsApiPool
    from routeros_api.exceptions import RouterOsApiError
    ROUTEROS_AVAILABLE = True
except ImportError:
    ROUTEROS_AVAILABLE = False

from ..models.device import Device
from .device_service import decrypt_secret
from ..config import Config

logger = logging.getLogger(__name__)

class DeviceMiner:
    """
    Miner class to extract forensic data from a specific device.
    """
    def __init__(self, device: Device):
        self.device = device
        self.host = getattr(device, "ip_address", None) or getattr(device, "host", None)
        self.port = self._resolve_port()
        self.timeout = int(getattr(Config, "MT_TIMEOUT_SEC", 5) or 5)
        self.api = None
        self.pool = None
        self.ros_version_major = None

    def _resolve_port(self) -> int:
        for attr in ("ros_api_port", "api_port", "routeros_port", "port"):
            value = getattr(self.device, attr, None)
            if value and str(value).isdigit():
                val_int = int(value)
                if attr == "port" and val_int == 22: # Skip SSH port if mixed up
                    continue
                return val_int
        return 8728

    def _connect(self):
        if not ROUTEROS_AVAILABLE:
            raise RuntimeError("routeros_api library not installed.")

        try:
            username = decrypt_secret(self.device.username_encrypted)
            password = decrypt_secret(self.device.password_encrypted)
        except Exception as e:
            raise ValueError(f"Credential decryption failed: {e}")

        self.pool = RouterOsApiPool(
            self.host,
            username=username,
            password=password,
            port=self.port,
            plaintext_login=True,
            use_ssl=False,
            socket_timeout=self.timeout
        )
        self.api = self.pool.get_api()

    def _disconnect(self):
        if self.pool:
            try:
                self.pool.disconnect()
            except:
                pass

    def mine(self) -> Dict[str, Any]:
        """
        Main entry point to mine data.
        Returns a structured dictionary with all gathered contexts.
        """
        if not self.host:
            logger.warning(f"Device {self.device.id} has no host.")
            return {}

        data = {
            "device_id": self.device.id,
            "timestamp": datetime.utcnow().isoformat(),
            "context": {},
            "health": {},
            "interfaces": [],
            "layer3": {},
            "security": {},
            "wireless": [], # New field for Wifi
            "logs": [],
            "heuristics": []
        }

        try:
            self._connect()

            # 1. Context Base (Identity, Resource, Routerboard, Package)
            data["context"] = self._get_base_context()

            # Determine version for subsequent commands
            version_str = data["context"].get("version", "")
            self.ros_version_major = 7 if version_str.startswith("7") else 6

            # 2. Health
            data["health"] = self._get_health()

            # 3. Layer 1 & 2 (Interfaces)
            data["interfaces"] = self._get_interfaces()

            # Wireless/Wifi clients
            data["wireless"] = self._get_wireless_clients()

            # 4. Layer 3 & Topology
            data["layer3"] = self._get_layer3()

            # 5. Security
            data["security"] = self._get_security()

            # 6. Logs (Standard /log/print)
            data["logs"] = self._get_logs()

        except Exception as e:
            logger.error(f"Mining failed for device {self.device.id}: {e}")
            data["error"] = str(e)
        finally:
            self._disconnect()

        # 7. Local Forensic Heuristics (Pre-processing)
        data["heuristics"] = self._apply_forensic_heuristics(data)

        return data

    def _safe_get(self, resource_path: str, params: Dict = None) -> List[Dict]:
        """Helper to safely execute an API call."""
        try:
            res = self.api.get_resource(resource_path)
            if params:
                return res.get(**params)
            return res.get()
        except Exception as e:
            logger.debug(f"Failed to get {resource_path}: {e}")
            return []

    def _safe_call(self, resource_path: str, command: str, arguments: Dict = None) -> List[Dict]:
        """Helper to call a command (e.g. print with specific args)"""
        try:
            res = self.api.get_resource(resource_path)
            return res.call(command, arguments or {})
        except Exception as e:
            logger.debug(f"Failed to call {command} on {resource_path}: {e}")
            return []

    def _get_base_context(self) -> Dict[str, Any]:
        context = {}
        # Identity
        identity = self._safe_get('/system/identity')
        context["identity"] = identity[0].get('name') if identity else "Unknown"

        # Resources
        resources = self._safe_get('/system/resource')
        if resources:
            res = resources[0]
            context.update({
                "uptime": res.get("uptime"),
                "cpu_load": res.get("cpu-load"),
                "free_memory": res.get("free-memory"),
                "total_memory": res.get("total-memory"),
                "version": res.get("version"),
                "board_name": res.get("board-name")
            })

        # Routerboard
        routerboard = self._safe_get('/system/routerboard')
        if routerboard:
            rb = routerboard[0]
            context["serial_number"] = rb.get("serial-number")
            context["firmware"] = rb.get("current-firmware")

        return context

    def _get_health(self) -> Dict[str, Any]:
        health_data = {}
        # /system/health/print
        items = self._safe_get('/system/health')
        for item in items:
            name = item.get("name")
            val = item.get("value")
            if name and val:
                health_data[name] = val
        return health_data

    def _get_interfaces(self) -> List[Dict[str, Any]]:
        # /interface/print stats-detail
        interfaces = self._safe_get('/interface')
        ethers = {e.get('name'): e for e in self._safe_get('/interface/ethernet')}

        enhanced_interfaces = []
        for iface in interfaces:
            name = iface.get("name")
            eth_info = ethers.get(name, {})

            stats = {
                "name": name,
                "type": iface.get("type"),
                "running": iface.get("running") == "true",
                "disabled": iface.get("disabled") == "true",
                "rx_byte": iface.get("rx-byte"),
                "tx_byte": iface.get("tx-byte"),
                "rx_error": iface.get("rx-error"),
                "tx_error": iface.get("tx-error"),
                "rx_drop": iface.get("rx-drop"),
                "tx_drop": iface.get("tx-drop"),
                "fp_rx_byte": iface.get("fp-rx-byte"),
                "fp_tx_byte": iface.get("fp-tx-byte"),
                "rx_fcs_error": iface.get("rx-fcs-error") or iface.get("fcs-error"),

                "auto_negotiation": eth_info.get("auto-negotiation"),
                "speed": eth_info.get("speed"),
                "full_duplex": eth_info.get("full-duplex")
            }
            enhanced_interfaces.append(stats)

        return enhanced_interfaces

    def _get_wireless_clients(self) -> List[Dict[str, Any]]:
        # v6: /interface wireless registration-table
        # v7: /interface wifiwave2 registration-table OR /interface wifi registration-table
        clients = []

        if self.ros_version_major == 6:
            clients = self._safe_get('/interface/wireless/registration-table')
        else:
            # Try wifiwave2 first, then wifi, then legacy wireless
            clients = self._safe_get('/interface/wifiwave2/registration-table')
            if not clients:
                 clients = self._safe_get('/interface/wifi/registration-table')
            if not clients:
                 clients = self._safe_get('/interface/wireless/registration-table')

        # Simplify output
        simple_clients = []
        for c in clients:
            simple_clients.append({
                "interface": c.get("interface"),
                "mac": c.get("mac-address"),
                "signal": c.get("signal-strength"),
                "tx_rate": c.get("tx-rate"),
                "rx_rate": c.get("rx-rate")
            })
        return simple_clients

    def _get_layer3(self) -> Dict[str, Any]:
        l3 = {}

        # IP Addresses
        ips = self._safe_get('/ip/address')
        l3["addresses"] = [
            {"address": i.get("address"), "interface": i.get("interface")}
            for i in ips
        ]

        # Neighbors
        neighbors = self._safe_get('/ip/neighbor')
        l3["neighbors"] = [
            {"interface": n.get("interface"), "ip": n.get("address"), "mac": n.get("mac-address"), "identity": n.get("identity")}
            for n in neighbors
        ]

        # Routes: /ip/route/print count-only
        # In API, getting resource counts directly is not standard in 'get'.
        # We try to use the 'print' command with 'count-only' argument if supported by python wrapper.
        # But 'call' returns list.
        # Workaround: Fetch stats from /routing/route if v7, or just count visible.
        # Or execute `/ip/route/print count-only` via safe_call

        # Try count-only via call. Note: parameters in call are usually dict.
        # api.get_resource('/ip/route').call('print', {'count-only': ''})

        route_count = 0
        try:
            # This returns a list containing one dict like { "ret": 123 } or similar depending on version/lib
            res = self._safe_call('/ip/route', 'print', {'count-only': ''})
            # routeros_api might not parse the integer return of count-only well, usually it expects list of items.
            # If it fails, we default to "Unknown".
            if res and isinstance(res, list) and 'ret' in res[0]:
                 # Sometimes 'ret' is not there for count-only in API
                 pass
            # Fallback: if we can't count reliably without fetching all, we skip exact count.
            # Instead, we check dynamic protocols presence.
        except:
            pass

        l3["route_summary"] = "Count lookup skipped (API limitation)"

        # Check for dynamic protocols (OSPF/BGP)
        # We can check /routing/ospf/neighbor or /routing/bgp/session
        dynamic_protocols = []
        if self._safe_get('/routing/ospf/neighbor') or self._safe_get('/routing/ospf/interface'):
            dynamic_protocols.append("OSPF")
        if self._safe_get('/routing/bgp/peer') or self._safe_get('/routing/bgp/connection'):
            dynamic_protocols.append("BGP")

        l3["active_protocols"] = dynamic_protocols

        return l3

    def _get_security(self) -> Dict[str, Any]:
        sec = {}
        # /ip/firewall/filter/print stats
        # We just get the rules and look at bytes/packets
        rules = self._safe_get('/ip/firewall/filter')

        # Summarize dropped packets
        drop_count = 0
        for rule in rules:
            if rule.get("action") == "drop":
                packets = int(rule.get("packets", 0))
                drop_count += packets

        sec["total_fw_drop_packets"] = drop_count
        return sec

    def _get_logs(self) -> List[Dict[str, Any]]:
        # Reuse existing logic logic or call API directly
        # We limit to last 50 logs for context
        logs = self._safe_call('/log', 'print')
        # Sort or slice might be needed if API returns all
        # Usually API returns all buffer.
        return logs[-50:] if logs else []

    def _apply_forensic_heuristics(self, data: Dict[str, Any]) -> List[str]:
        findings = []

        # 1. CPU & Traffic (DDoS/Loop)
        cpu = 0
        try:
            cpu = int(data["context"].get("cpu_load", 0))
        except: pass

        # 2. Interface Errors
        for iface in data.get("interfaces", []):
            name = iface.get("name")
            fcs = int(iface.get("rx_fcs_error") or 0)
            if fcs > 0:
                findings.append(f"Interface {name} has {fcs} FCS errors. Suggests physical cable/connector damage.")

            rx_drop = int(iface.get("rx_drop") or 0)
            if rx_drop > 100:
                findings.append(f"Interface {name} has high RX drops ({rx_drop}). Possible congestion or flow control issue.")

        # 3. Voltage/Power
        health = data.get("health", {})
        voltage = health.get("voltage")
        if voltage:
            try:
                v = float(voltage)
                # Heuristic: < 10V is suspicious for most 12V/24V systems
                if v < 10:
                    findings.append(f"Low voltage detected: {v}V. Check Power Supply.")
            except: pass

        # 4. CPU High
        if cpu > 90:
            findings.append("CPU is critical (>90%).")

        return findings
