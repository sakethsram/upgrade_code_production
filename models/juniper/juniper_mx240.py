# mx240_models.py
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from dataclasses import asdict
# ────────────────────────────────────────────────────────────────────────────────
# show services flows brief | no-more
# ────────────────────────────────────────────────────────────────────────────────

@dataclass
class ShowServicesFlowsBriefEntry:
    flow_id: str = ""
    interface: str = ""
    service_set: str = ""
    direction: str = ""
    protocol: str = ""
    src_address: str = ""
    dst_address: str = ""
    src_port: str = ""
    dst_port: str = ""
    packets: int = 0
    bytes: int = 0

@dataclass
class ShowServicesFlowsBrief:
    flows: List[ShowServicesFlowsBriefEntry] = field(default_factory=list)
    total_flows: int = 0

    def to_dict(self) -> dict:
        return {
            "total_flows": self.total_flows,
            "flows": [
                {
                    "flow_id":      f.flow_id,
                    "interface":    f.interface,
                    "service_set":  f.service_set,
                    "direction":    f.direction,
                    "protocol":     f.protocol,
                    "src_address":  f.src_address,
                    "dst_address":  f.dst_address,
                    "src_port":     f.src_port,
                    "dst_port":     f.dst_port,
                    "packets":      f.packets,
                    "bytes":        f.bytes,
                }
                for f in self.flows
            ],
        }


# ────────────────────────────────────────────────────────────────────────────────
# show chassis alarms | no-more
# ────────────────────────────────────────────────────────────────────────────────

@dataclass
class AlarmEntry:
    alarm_time: str = ""
    alarm_class: str = ""
    description: str = ""

@dataclass
class ShowChassisAlarms:
    alarm_count: int = 0
    alarms: List[AlarmEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "alarm_count": self.alarm_count,
            "alarms": [
                {
                    "alarm_time":  a.alarm_time,
                    "alarm_class": a.alarm_class,
                    "description": a.description,
                }
                for a in self.alarms
            ],
        }


# ────────────────────────────────────────────────────────────────────────────────
# show system alarms | no-more
# ────────────────────────────────────────────────────────────────────────────────

@dataclass
class ShowSystemAlarms:
    alarm_count: int = 0
    alarms: List[AlarmEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "alarm_count": self.alarm_count,
            "alarms": [
                {
                    "alarm_time":  a.alarm_time,
                    "alarm_class": a.alarm_class,
                    "description": a.description,
                }
                for a in self.alarms
            ],
        }


# ────────────────────────────────────────────────────────────────────────────────
# show oam ethernet connectivity-fault-management interfaces extensive | no-more
# ────────────────────────────────────────────────────────────────────────────────

@dataclass
class OamCfmInterface:
    interface_name: str = ""
    interface_status: str = ""
    link_status: str = ""
    maintenance_domain_name: str = ""
    md_format: str = ""
    md_level: Optional[int] = None
    md_index: Optional[int] = None
    maintenance_association_name: str = ""
    ma_format: str = ""
    ma_index: Optional[int] = None
    continuity_check_status: str = ""
    cc_interval: str = ""
    loss_threshold: str = ""
    mep_identifier: Optional[int] = None
    mep_direction: str = ""
    mac_address: str = ""
    mep_status: str = ""

@dataclass
class ShowOamCfmInterfaces:
    interfaces: List[OamCfmInterface] = field(default_factory=list)
    subsystem_not_running: bool = False

    def to_dict(self) -> dict:
        return {
            "subsystem_not_running": self.subsystem_not_running,
            "total_interfaces": len(self.interfaces),
            "interfaces": [
                {
                    "interface_name":              i.interface_name,
                    "interface_status":            i.interface_status,
                    "link_status":                 i.link_status,
                    "maintenance_domain_name":     i.maintenance_domain_name,
                    "md_format":                   i.md_format,
                    "md_level":                    i.md_level,
                    "md_index":                    i.md_index,
                    "maintenance_association_name": i.maintenance_association_name,
                    "ma_format":                   i.ma_format,
                    "ma_index":                    i.ma_index,
                    "continuity_check_status":     i.continuity_check_status,
                    "cc_interval":                 i.cc_interval,
                    "loss_threshold":              i.loss_threshold,
                    "mep_identifier":              i.mep_identifier,
                    "mep_direction":               i.mep_direction,
                    "mac_address":                 i.mac_address,
                    "mep_status":                  i.mep_status,
                }
                for i in self.interfaces
            ],
        }

@dataclass
class BgpSummaryTableEntry:
    table_name: str
    tot_paths: int
    act_paths: int
    suppressed: int
    history: int
    damp_state: int
    pending: int


@dataclass
class BgpSummaryPeerEntry:
    peer: str
    asn: str
    in_pkt: int
    out_pkt: int
    out_q: int
    flaps: int
    last_up_dwn: str
    state: str
    table_counts: List[Dict[str, Any]] = field(default_factory=list)
    state_detail: str = ""


@dataclass
class ShowBgpSummary:
    groups: int = 0
    peers: int = 0
    down_peers: int = 0
    tables: List[BgpSummaryTableEntry] = field(default_factory=list)
    peer_entries: List[BgpSummaryPeerEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "groups": self.groups,
            "peers": self.peers,
            "down_peers": self.down_peers,
            "tables": [
                {
                    "table_name": t.table_name,
                    "tot_paths": t.tot_paths,
                    "act_paths": t.act_paths,
                    "suppressed": t.suppressed,
                    "history": t.history,
                    "damp_state": t.damp_state,
                    "pending": t.pending,
                }
                for t in self.tables
            ],
            "peers": [
                {
                    "peer": p.peer,
                    "asn": p.asn,
                    "in_pkt": p.in_pkt,
                    "out_pkt": p.out_pkt,
                    "out_q": p.out_q,
                    "flaps": p.flaps,
                    "last_up_dwn": p.last_up_dwn,
                    "state": p.state,
                    "state_detail": p.state_detail,
                    "table_counts": p.table_counts,
                }
                for p in self.peer_entries
            ],
        }


@dataclass
class BgpNeighborTable:
    table_name: str
    rib_state_bgp: str
    rib_state_vpn: str
    send_state: str
    active_prefixes: int
    received_prefixes: int
    accepted_prefixes: int
    suppressed_damping: int
    advertised_prefixes: Optional[int]


@dataclass
class BgpNeighborEntry:
    peer_ip: str
    peer_as: str
    local_ip: str
    local_as: str
    description: str
    group: str
    routing_instance: str
    forwarding_instance: str
    peer_type: str
    state: str
    flags: str
    last_state: str
    last_event: str
    last_error: str
    export_policies: List[str]
    import_policies: List[str]
    options: List[str]
    holdtime: int
    local_address: str
    keepalive_interval: Optional[int]
    bfd: str
    local_interface: str
    nlri_families: List[str]
    peer_id: str
    local_id: str
    active_holdtime: Optional[int]
    num_flaps: int
    last_flap_event: str
    last_traffic_received_sec: Optional[int]
    last_traffic_sent_sec: Optional[int]
    input_messages_total: Optional[int]
    input_messages_updates: Optional[int]
    output_messages_total: Optional[int]
    output_messages_updates: Optional[int]
    tables: List[BgpNeighborTable] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "peer_ip": self.peer_ip,
            "peer_as": self.peer_as,
            "local_ip": self.local_ip,
            "local_as": self.local_as,
            "description": self.description,
            "group": self.group,
            "routing_instance": self.routing_instance,
            "forwarding_instance": self.forwarding_instance,
            "peer_type": self.peer_type,
            "state": self.state,
            "flags": self.flags,
            "last_state": self.last_state,
            "last_event": self.last_event,
            "last_error": self.last_error,
            "export_policies": self.export_policies,
            "import_policies": self.import_policies,
            "options": self.options,
            "holdtime": self.holdtime,
            "local_address": self.local_address,
            "keepalive_interval": self.keepalive_interval,
            "bfd": self.bfd,
            "local_interface": self.local_interface,
            "nlri_families": self.nlri_families,
            "peer_id": self.peer_id,
            "local_id": self.local_id,
            "active_holdtime": self.active_holdtime,
            "num_flaps": self.num_flaps,
            "last_flap_event": self.last_flap_event,
            "last_traffic_received_sec": self.last_traffic_received_sec,
            "last_traffic_sent_sec": self.last_traffic_sent_sec,
            "input_messages_total": self.input_messages_total,
            "input_messages_updates": self.input_messages_updates,
            "output_messages_total": self.output_messages_total,
            "output_messages_updates": self.output_messages_updates,
            "tables": [
                {
                    "table_name": t.table_name,
                    "rib_state_bgp": t.rib_state_bgp,
                    "rib_state_vpn": t.rib_state_vpn,
                    "send_state": t.send_state,
                    "active_prefixes": t.active_prefixes,
                    "received_prefixes": t.received_prefixes,
                    "accepted_prefixes": t.accepted_prefixes,
                    "suppressed_damping": t.suppressed_damping,
                    "advertised_prefixes": t.advertised_prefixes,
                }
                for t in self.tables
            ],
        }


@dataclass
class ShowBgpNeighbor:
    neighbors: List[BgpNeighborEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_neighbors": len(self.neighbors),
            "neighbors": [n.to_dict() for n in self.neighbors],
        }


# ── show services sessions | no-more ────────────────────────────────────────

@dataclass
class ServiceSessionFlow:
    protocol:       str = ""
    src_ip:         str = ""
    src_port:       int = 0
    dst_ip:         str = ""
    dst_port:       int = 0
    direction:      str = ""   # Forward / Reverse
    flow_dir:       str = ""   # I / O
    packets:        int = 0


@dataclass
class ServiceSession:
    interface:      str = ""
    service_set:    str = ""
    session_id:     int = 0
    alg:            str = "none"
    flags:          str = "0x0"
    ip_action:      str = "no"
    offload:        str = "no"
    asymmetric:     str = "no"
    flows:          List[ServiceSessionFlow] = field(default_factory=list)


@dataclass
class ShowServicesSessions:
    sessions:       List[ServiceSession] = field(default_factory=list)
    total_sessions: int = 0

    def to_dict(self) -> dict:
        return {
            "total_sessions": self.total_sessions,
            "sessions": [
                {
                    "interface":    s.interface,
                    "service_set":  s.service_set,
                    "session_id":   s.session_id,
                    "alg":          s.alg,
                    "flags":        s.flags,
                    "ip_action":    s.ip_action,
                    "offload":      s.offload,
                    "asymmetric":   s.asymmetric,
                    "flows": [
                        {
                            "protocol":  f.protocol,
                            "src_ip":    f.src_ip,
                            "src_port":  f.src_port,
                            "dst_ip":    f.dst_ip,
                            "dst_port":  f.dst_port,
                            "direction": f.direction,
                            "flow_dir":  f.flow_dir,
                            "packets":   f.packets,
                        }
                        for f in s.flows
                    ],
                }
                for s in self.sessions
            ],
        }


# ── show services nat pool brief | no-more ──────────────────────────────────

@dataclass
class NatPoolEntry:
    pool_name:      str = ""
    nat_type:       str = ""   # NAPT-44, DNAT-44, etc.
    address_range:  str = ""   # "10.9.142.4-10.9.142.4"
    port_range:     str = ""   # "1024-65535" or "" for DNAT
    ports_used:     Optional[int] = None


@dataclass
class NatPoolInterface:
    interface:      str = ""
    service_set:    str = ""
    pools:          List[NatPoolEntry] = field(default_factory=list)


@dataclass
class ShowServicesNatPoolBrief:
    interfaces:     List[NatPoolInterface] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "interfaces": [
                {
                    "interface":   i.interface,
                    "service_set": i.service_set,
                    "pools": [
                        {
                            "pool_name":     p.pool_name,
                            "nat_type":      p.nat_type,
                            "address_range": p.address_range,
                            "port_range":    p.port_range,
                            "ports_used":    p.ports_used,
                        }
                        for p in i.pools
                    ],
                }
                for i in self.interfaces
            ]
        }


# ── show services service-sets cpu-usage | no-more ──────────────────────────

@dataclass
class ServiceSetCpuEntry:
    interface:      str = ""
    service_set:    str = ""
    cpu_utilization: float = 0.0   # percentage, e.g. 1.42


@dataclass
class ShowServicesServiceSetsCpuUsage:
    entries:        List[ServiceSetCpuEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "entries": [
                {
                    "interface":       e.interface,
                    "service_set":     e.service_set,
                    "cpu_utilization": e.cpu_utilization,
                }
                for e in self.entries
            ]
        }


# ── show services service-sets memory-usage | no-more ───────────────────────

@dataclass
class ServiceSetMemoryEntry:
    interface:      str = ""
    service_set:    str = ""
    bytes_used:     int = 0


@dataclass
class ShowServicesServiceSetsMemoryUsage:
    entries:        List[ServiceSetMemoryEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "entries": [
                {
                    "interface":   e.interface,
                    "service_set": e.service_set,
                    "bytes_used":  e.bytes_used,
                }
                for e in self.entries
            ]
        }


# ── show services service-sets summary | no-more ────────────────────────────

@dataclass
class ServiceSetSummaryEntry:
    interface:              str   = ""
    service_sets_configured: int  = 0
    bytes_used:             int   = 0
    bytes_used_pct:         float = 0.0
    policy_bytes_used:      int   = 0
    policy_bytes_used_pct:  float = 0.0
    cpu_utilization:        float = 0.0


@dataclass
class ShowServicesServiceSetsSummary:
    entries:        List[ServiceSetSummaryEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "entries": [
                {
                    "interface":               e.interface,
                    "service_sets_configured": e.service_sets_configured,
                    "bytes_used":              e.bytes_used,
                    "bytes_used_pct":          e.bytes_used_pct,
                    "policy_bytes_used":       e.policy_bytes_used,
                    "policy_bytes_used_pct":   e.policy_bytes_used_pct,
                    "cpu_utilization":         e.cpu_utilization,
                }
                for e in self.entries
            ]
        }
