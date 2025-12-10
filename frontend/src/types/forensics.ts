/**
 * Type Definitions for Forensic Data
 * Matches the JSON structure returned by the Backend DeviceMiner & AI Provider.
 */

export interface InterfaceStats {
    name: string;
    type: string;
    running: boolean;
    disabled: boolean;
    rx_byte?: string;
    tx_byte?: string;
    rx_error?: string;
    tx_error?: string;
    rx_drop?: string;
    tx_drop?: string;
    rx_fcs_error?: string; // Critical for physical health
    auto_negotiation?: string;
    speed?: string;
    full_duplex?: string;
}

export interface NeighborInfo {
    interface: string;
    ip: string;
    mac?: string;
    identity?: string;
    platform?: string;
}

export interface DeviceHealth {
    voltage?: string;
    temperature?: string;
}

export interface DeviceContext {
    identity: string;
    version: string;
    uptime: string;
    cpu_load?: string;
    board_name?: string;
    serial_number?: string;
    firmware?: string;
}

export interface Layer3Topology {
    addresses: Array<{ address: string; interface: string }>;
    neighbors: NeighborInfo[];
    route_summary?: string;
    active_protocols?: string[];
}

export interface TelemetryData {
    critical_logs?: string[];
    interface_errors?: Record<string, string>;
    resource_stress?: string;
    [key: string]: any;
}

export interface AIDiagnosisJSON {
    context: {
        model: string;
        ros_version: string;
        uptime: string;
    };
    telemetry: TelemetryData;
    analysis: string; // Detailed root cause
    recommendations: string[];
    estado?: "Aviso" | "Alerta Menor" | "Alerta Severa" | "Alerta Crítica";
}

export interface MiningDataResponse {
    device_id: number;
    timestamp: string;
    context: DeviceContext;
    health: DeviceHealth;
    interfaces: InterfaceStats[];
    layer3: Layer3Topology;
    security: { total_fw_drop_packets?: number };
    logs: any[];
    heuristics: string[];
    diagnosis?: AIDiagnosisJSON; // Merged from AI Analysis
}
