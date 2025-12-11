"""
Servicio de Minería de Datos de Dispositivos (Device Mining).

Responsable de establecer conexión con dispositivos Mikrotik y extraer datos forenses profundos.
Maneja diferencias de versión (RouterOS v6 vs v7), gestión de errores y estructuración de datos.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

# Intento de importación de routeros_api, manejo elegante de dependencia faltante
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
    Clase minera encargada de extraer datos forenses de un dispositivo específico.
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
        """Determina el puerto API correcto a utilizar."""
        for attr in ("ros_api_port", "api_port", "routeros_port", "port"):
            value = getattr(self.device, attr, None)
            if value and str(value).isdigit():
                val_int = int(value)
                if attr == "port" and val_int == 22: # Omitir puerto SSH si hubo confusión
                    continue
                return val_int
        return 8728

    def _connect(self):
        """Establece la conexión con el dispositivo vía RouterOS API."""
        if not ROUTEROS_AVAILABLE:
            raise RuntimeError("[ERROR] La librería routeros_api no está instalada.")

        try:
            username = decrypt_secret(self.device.username_encrypted)
            password = decrypt_secret(self.device.password_encrypted)
        except Exception as e:
            raise ValueError(f"[ERROR] Fallo en descifrado de credenciales: {e}")

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
        """Cierra la conexión con el dispositivo."""
        if self.pool:
            try:
                self.pool.disconnect()
            except:
                pass

    def mine(self) -> Dict[str, Any]:
        """
        Punto de entrada principal para la minería de datos.

        Returns:
            Dict[str, Any]: Diccionario estructurado con todos los contextos recopilados
                            (contexto, salud, interfaces, capa3, seguridad, logs, heurística).
        """
        if not self.host:
            logger.warning(f"[WARNING] Dispositivo {self.device.id} no tiene host definido.")
            return {}

        data = {
            "device_id": self.device.id,
            "timestamp": datetime.utcnow().isoformat(),
            "context": {},
            "health": {},
            "interfaces": [],
            "layer3": {},
            "security": {},
            "wireless": [], # Nuevo campo para clientes Wifi
            "logs": [],
            "heuristics": []
        }

        try:
            self._connect()

            # 1. Contexto Base (Identidad, Recursos, Routerboard)
            data["context"] = self._get_base_context()

            # Determinar versión para comandos subsiguientes
            version_str = data["context"].get("version", "")
            self.ros_version_major = 7 if version_str.startswith("7") else 6

            # 2. Salud (Health)
            data["health"] = self._get_health()

            # 3. Capa 1 & 2 (Interfaces)
            data["interfaces"] = self._get_interfaces()

            # Clientes Inalámbricos/Wifi
            data["wireless"] = self._get_wireless_clients()

            # 4. Capa 3 & Topología
            data["layer3"] = self._get_layer3()

            # 5. Seguridad
            data["security"] = self._get_security()

            # 6. Logs (Estándar /log/print)
            data["logs"] = self._get_logs()

        except Exception as e:
            logger.error(f"[ERROR] Falló la minería para dispositivo {self.device.id}: {e}")
            data["error"] = str(e)
        finally:
            self._disconnect()

        # 7. Heurística Forense Local (Pre-procesamiento)
        data["heuristics"] = self._apply_forensic_heuristics(data)

        return data

    def _safe_get(self, resource_path: str, params: Dict = None) -> List[Dict]:
        """Helper para ejecutar una llamada API de forma segura."""
        try:
            res = self.api.get_resource(resource_path)
            if params:
                return res.get(**params)
            return res.get()
        except Exception as e:
            logger.debug(f"[DEBUG] Falló al obtener {resource_path}: {e}")
            return []

    def _safe_call(self, resource_path: str, command: str, arguments: Dict = None) -> List[Dict]:
        """Helper para invocar un comando (ej. print con argumentos específicos)."""
        try:
            res = self.api.get_resource(resource_path)
            return res.call(command, arguments or {})
        except Exception as e:
            logger.debug(f"[DEBUG] Falló al llamar {command} en {resource_path}: {e}")
            return []

    def _get_base_context(self) -> Dict[str, Any]:
        context = {}
        # Identidad
        identity = self._safe_get('/system/identity')
        context["identity"] = identity[0].get('name') if identity else "Desconocido"

        # Recursos
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
        # v7: /interface wifiwave2 registration-table O /interface wifi registration-table
        clients = []

        if self.ros_version_major == 6:
            clients = self._safe_get('/interface/wireless/registration-table')
        else:
            # Intentar wifiwave2 primero, luego wifi, luego legacy wireless
            clients = self._safe_get('/interface/wifiwave2/registration-table')
            if not clients:
                 clients = self._safe_get('/interface/wifi/registration-table')
            if not clients:
                 clients = self._safe_get('/interface/wireless/registration-table')

        # Simplificar salida
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

        # Direcciones IP
        ips = self._safe_get('/ip/address')
        l3["addresses"] = [
            {"address": i.get("address"), "interface": i.get("interface")}
            for i in ips
        ]

        # Vecinos (Neighbors)
        neighbors = self._safe_get('/ip/neighbor')
        l3["neighbors"] = [
            {"interface": n.get("interface"), "ip": n.get("address"), "mac": n.get("mac-address"), "identity": n.get("identity")}
            for n in neighbors
        ]

        # Rutas
        l3["route_summary"] = "Conteo omitido (Limitación API)"

        # Detección de protocolos dinámicos (OSPF/BGP)
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
        # Obtenemos reglas y sumamos bytes/paquetes de drops
        rules = self._safe_get('/ip/firewall/filter')

        # Resumir paquetes descartados (dropped)
        drop_count = 0
        for rule in rules:
            if rule.get("action") == "drop":
                packets = int(rule.get("packets", 0))
                drop_count += packets

        sec["total_fw_drop_packets"] = drop_count
        return sec

    def _get_logs(self) -> List[Dict[str, Any]]:
        # Limitamos a los últimos 50 logs para contexto
        logs = self._safe_call('/log', 'print')
        return logs[-50:] if logs else []

    def _apply_forensic_heuristics(self, data: Dict[str, Any]) -> List[str]:
        findings = []

        # 1. CPU & Tráfico (DDoS/Bucle)
        cpu = 0
        try:
            cpu = int(data["context"].get("cpu_load", 0))
        except: pass

        # 2. Errores de Interfaz
        for iface in data.get("interfaces", []):
            name = iface.get("name")
            fcs = int(iface.get("rx_fcs_error") or 0)
            if fcs > 0:
                findings.append(f"Interfaz {name} tiene {fcs} errores FCS. Sugiere daño físico en cable/conector.")

            rx_drop = int(iface.get("rx_drop") or 0)
            if rx_drop > 100:
                findings.append(f"Interfaz {name} tiene altos descartes RX ({rx_drop}). Posible congestión o problema de control de flujo.")

        # 3. Voltaje/Energía
        health = data.get("health", {})
        voltage = health.get("voltage")
        if voltage:
            try:
                v = float(voltage)
                # Heurística: < 10V es sospechoso para sistemas de 12V/24V
                if v < 10:
                    findings.append(f"Bajo voltaje detectado: {v}V. Verificar fuente de alimentación.")
            except: pass

        # 4. CPU Crítico
        if cpu > 90:
            findings.append("Uso de CPU crítico (>90%).")

        return findings
