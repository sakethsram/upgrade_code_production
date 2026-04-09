# mx240_parsers.py
import re
from dataclasses import asdict
from typing import Any, Dict

import re
from typing import Any, Dict, List, Optional
# from models.juniper.juniper_mx240 import (
#     ShowBgpSummary,
#     BgpSummaryTableEntry,
#     BgpSummaryPeerEntry,

#     ShowBgpNeighbor,
#     BgpNeighborEntry,
#     BgpNeighborTable,

#     ShowServicesSessions,
#     ServiceSession,
#     ServiceSessionFlow,

#     ShowServicesNatPoolBrief,
#     NatPoolInterface,
#     NatPoolEntry,

#     ShowServicesServiceSetsCpuUsage,
#     ServiceSetCpuEntry,

#     ShowServicesServiceSetsMemoryUsage,
#     ServiceSetMemoryEntry,

#     ShowServicesServiceSetsSummary,
#     ServiceSetSummaryEntry,

#     ShowServicesFlowsBrief,
#     ShowServicesFlowsBriefEntry,

#     ShowChassisAlarms,
#     ShowSystemAlarms,
#     AlarmEntry,

#     ShowOamCfmInterfaces,
#     OamCfmInterface,
# )
from models.juniper.juniper_mx240 import *
def parse_show_bgp_summary(text_content: str) -> Dict[str, Any]:
    cmd = "show bgp summary | no-more"
    try:
        result = ShowBgpSummary()

        # ── header ────────────────────────────────────────────────────────────
        hdr = re.search(
            r"Groups:\s*(\d+)\s+Peers:\s*(\d+)\s+Down peers:\s*(\d+)",
            text_content,
        )
        if hdr:
            result.groups     = int(hdr.group(1))
            result.peers      = int(hdr.group(2))
            result.down_peers = int(hdr.group(3))

        # ── per-table path counts ─────────────────────────────────────────────
        table_section_m = re.search(
            r"^Table\s+Tot Paths.*?(?=^Peer\s+AS\s+InPkt)",
            text_content,
            re.MULTILINE | re.DOTALL,
        )
        if table_section_m:
            for m in re.finditer(
                r"^(\S+)\s*\n\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
                table_section_m.group(),
                re.MULTILINE,
            ):
                result.tables.append(
                    BgpSummaryTableEntry(
                        table_name = m.group(1),
                        tot_paths  = int(m.group(2)),
                        act_paths  = int(m.group(3)),
                        suppressed = int(m.group(4)),
                        history    = int(m.group(5)),
                        damp_state = int(m.group(6)),
                        pending    = int(m.group(7)),
                    )
                )
        # ── peer rows ─────────────────────────────────────────────────────────
        peer_line_re = re.compile(
            r"^(\d{1,3}(?:\.\d{1,3}){3}(?:\+\d+)?)\s+"
            r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)(.*)?$",
            re.MULTILINE,
        )
        table_detail_re = re.compile(
            r"^\s{2,}(\S+):\s+(\d+)/(\d+)/(\d+)/(\d+)\s*$",
            re.MULTILINE,
        )

        lines = text_content.splitlines()
        peer_header_idx = next(
            (i for i, l in enumerate(lines) if re.match(r"^Peer\s+AS\s+InPkt", l)),
            None,
        )

        if peer_header_idx is not None:
            peer_block = "\n".join(lines[peer_header_idx + 1:])
            current_peer = None

            for line in peer_block.splitlines():
                pm = peer_line_re.match(line)
                if pm:
                    current_peer = BgpSummaryPeerEntry(
                        peer         = pm.group(1),
                        asn          = pm.group(2),
                        in_pkt       = int(pm.group(3)),
                        out_pkt      = int(pm.group(4)),
                        out_q        = int(pm.group(5)),
                        flaps        = int(pm.group(6)),
                        last_up_dwn  = pm.group(7),
                        state        = pm.group(8),
                        state_detail = pm.group(9).strip() if pm.group(9) else "",
                    )
                    result.peer_entries.append(current_peer)
                elif current_peer is not None:
                    dm = table_detail_re.match(line)
                    if dm:
                        current_peer.table_counts.append({
                            "table":    dm.group(1),
                            "active":   int(dm.group(2)),
                            "received": int(dm.group(3)),
                            "accepted": int(dm.group(4)),
                            "damped":   int(dm.group(5)),
                        })

        return result.to_dict()

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
# ────────────────────────────────────────────────────────────────────────────────
def parse_show_bgp_neighbor(text_content: str) -> Dict[str, Any]:
    cmd = "show bgp neighbor | no-more"
    try:
        result = ShowBgpNeighbor()

        for block in re.split(r"(?=^Peer:\s+\d{1,3}(?:\.\d{1,3}){3})", text_content, flags=re.MULTILINE):
            block = block.strip()
            if not block or not re.match(r"Peer:\s+\d", block):
                continue

            # ── inline helpers (default arg captures current block) ───────────
            def _get(pattern: str, group: int = 1, default: str = "", _b: str = block) -> str:
                m = re.search(pattern, _b)
                return m.group(group).strip() if m else default

            def _get_int(pattern: str, group: int = 1, _b: str = block) -> Optional[int]:
                m = re.search(pattern, _b)
                return int(m.group(group)) if m else None

            # ── header line ───────────────────────────────────────────────────
            hdr = re.match(
                r"Peer:\s*(\S+)\s+AS\s+(\S+)\s+Local:\s*(\S+)\s+AS\s+(\S+)",
                block,
            )
            peer_ip  = hdr.group(1) if hdr else ""
            peer_as  = hdr.group(2) if hdr else ""
            local_ip = hdr.group(3) if hdr else ""
            local_as = hdr.group(4) if hdr else ""

            # ── scalar fields ─────────────────────────────────────────────────
            description         = _get(r"Description:\s*(.+)")
            group               = _get(r"Group:\s*(\S+)")
            routing_instance    = _get(r"Routing-Instance:\s*(\S+)")
            forwarding_instance = _get(r"Forwarding routing-instance:\s*(\S+)")
            peer_type           = _get(r"Type:\s*(\S+)")
            state               = _get(r"Type:\s*\S+\s+State:\s*(\S+)")
            flags               = _get(r"Flags:\s*<([^>]*)>")
            last_state          = _get(r"Last State:\s*(\S+)")
            last_event          = _get(r"Last Event:\s*(\S+)")
            last_error          = _get(r"Last Error:\s*(.+)")
            last_flap_event     = _get(r"Last flap event:\s*(\S+)")
            local_interface     = _get(r"Local Interface:\s*(\S+)")
            peer_id             = _get(r"Peer ID:\s*(\S+)")
            local_id            = _get(r"Local ID:\s*(\S+)")
            local_address       = _get(r"Local Address:\s*(\S+)")
            holdtime            = int(_get(r"Holdtime:\s*(\d+)", default="0") or 0)
            num_flaps           = int(_get(r"Number of flaps:\s*(\d+)", default="0") or 0)
            keepalive_interval  = _get_int(r"Keepalive Interval:\s*(\d+)")
            active_holdtime     = _get_int(r"Active Holdtime:\s*(\d+)")

            bfd_m = re.search(r"BFD:\s*(.*)", block)
            bfd   = bfd_m.group(1).strip() if bfd_m else ""

            # ── list fields ───────────────────────────────────────────────────
            export_policies = [
                p.strip()
                for raw in re.findall(r"Export:\s*\[([^\]]+)\]", block)
                for p in raw.split()
            ]
            import_policies = [
                p.strip()
                for raw in re.findall(r"Import:\s*\[([^\]]+)\]", block)
                for p in raw.split()
            ]
            options = [
                o.strip()
                for raw in re.findall(r"Options:\s*<([^>]*)>", block)
                for o in raw.split()
                if o.strip()
            ]

            nlri_families: List[str] = []
            nlri_m = re.search(r"Address families configured:\s*(.+)", block)
            if nlri_m:
                nlri_families = nlri_m.group(1).strip().split()
            else:
                nlri_s = re.search(r"NLRI for this session:\s*(.+)", block)
                if nlri_s:
                    nlri_families = nlri_s.group(1).strip().split()

            # ── counters ──────────────────────────────────────────────────────
            traffic_m = re.search(
                r"Last traffic \(seconds\):\s+Received\s+(\d+)\s+Sent\s+(\d+)", block
            )
            last_traffic_received_sec = int(traffic_m.group(1)) if traffic_m else None
            last_traffic_sent_sec     = int(traffic_m.group(2)) if traffic_m else None

            in_msg_m  = re.search(r"Input messages:\s+Total\s+(\d+)\s+Updates\s+(\d+)", block)
            out_msg_m = re.search(r"Output messages:\s+Total\s+(\d+)\s+Updates\s+(\d+)", block)
            input_messages_total    = int(in_msg_m.group(1))  if in_msg_m  else None
            input_messages_updates  = int(in_msg_m.group(2))  if in_msg_m  else None
            output_messages_total   = int(out_msg_m.group(1)) if out_msg_m else None
            output_messages_updates = int(out_msg_m.group(2)) if out_msg_m else None
            # ── per-table RIB detail ──────────────────────────────────────────
            tables: List[BgpNeighborTable] = []
            tbl_re = re.compile(
                r"Table\s+(\S+)\s+Bit:\s*\S+\s*\n"
                r".*?RIB State: BGP restart is (\S+)\s*\n"
                r".*?RIB State: VPN restart is (\S+)\s*\n"
                r".*?Send state:\s*(.+?)\s*\n"
                r".*?Active prefixes:\s*(\d+)\s*\n"
                r".*?Received prefixes:\s*(\d+)\s*\n"
                r".*?Accepted prefixes:\s*(\d+)\s*\n"
                r".*?Suppressed due to damping:\s*(\d+)",
                re.DOTALL,
            )

            adv_re = re.compile(r"Advertised prefixes:\s*(\d+)")

            for tb in re.split(r"(?=^\s{2}Table\s+\S+\s+Bit:)", block, flags=re.MULTILINE):
                m = tbl_re.search(tb)
                if not m:
                    continue

                adv_m = adv_re.search(tb[m.end(): m.end() + 200])
                tables.append(
                    BgpNeighborTable(
                        table_name          = m.group(1),
                        rib_state_bgp       = m.group(2),
                        rib_state_vpn       = m.group(3),
                        send_state          = m.group(4),
                        active_prefixes     = int(m.group(5)),
                        received_prefixes   = int(m.group(6)),
                        accepted_prefixes   = int(m.group(7)),
                        suppressed_damping  = int(m.group(8)),
                        advertised_prefixes = int(adv_m.group(1)) if adv_m else None,
                    )
                )

            result.neighbors.append(
                BgpNeighborEntry(
                    peer_ip                   = peer_ip,
                    peer_as                   = peer_as,
                    local_ip                  = local_ip,
                    local_as                  = local_as,
                    description               = description,
                    group                     = group,
                    routing_instance          = routing_instance,
                    forwarding_instance       = forwarding_instance,
                    peer_type                 = peer_type,
                    state                     = state,
                    flags                     = flags,
                    last_state                = last_state,
                    last_event                = last_event,
                    last_error                = last_error,
                    export_policies           = export_policies,
                    import_policies           = import_policies,
                    options                   = options,
                    holdtime                  = holdtime,
                    local_address             = local_address,
                    keepalive_interval        = keepalive_interval,
                    bfd                       = bfd,
                    local_interface           = local_interface,
                    nlri_families             = nlri_families,
                    peer_id                   = peer_id,
                    local_id                  = local_id,
                    active_holdtime           = active_holdtime,
                    num_flaps                 = num_flaps,
                    last_flap_event           = last_flap_event,
                    last_traffic_received_sec = last_traffic_received_sec,
                    last_traffic_sent_sec     = last_traffic_sent_sec,
                    input_messages_total      = input_messages_total,
                    input_messages_updates    = input_messages_updates,
                    output_messages_total     = output_messages_total,
                    output_messages_updates   = output_messages_updates,
                    tables                    = tables,
                )
            )

        output = result.to_dict()
        output["by_peer"] = {n["peer_ip"]: n for n in output["neighbors"]}
        return output

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
# ────────────────────────────────────────────────────────────────────────────
def parse_show_services_sessions(text_content: str) -> Dict[str, Any]:
    cmd = "show services sessions | no-more"
    try:
        result = ShowServicesSessions()
        current_iface = ""

        # Capture interface line  e.g. "ms-2/2/0"
        iface_re    = re.compile(r'^(ms-\S+)\s*$', re.MULTILINE)

        # Session header line
        session_re  = re.compile(
            r'Service Set:\s*(\S+),\s*Session:\s*(\d+),\s*ALG:\s*(\S+),\s*'
            r'Flags:\s*(\S+),\s*IP Action:\s*(\S+),\s*Offload:\s*(\S+),\s*Asymmetric:\s*(\S+)'
        )

        # Flow line  e.g.: TCP  1.2.3.4:100 -> 5.6.7.8:200  Forward  I  1234
        flow_re = re.compile(
            r'(TCP|UDP|ICMP|GRE)\s+'
            r'([\d.]+):(\d+)\s*->\s*([\d.]+):(\d+)\s+'
            r'(Forward|Reverse)\s+([IO])\s+(\d+)'
        )

        current_session: ServiceSession | None = None

        for line in text_content.splitlines():
            iface_match = iface_re.match(line.strip())
            if iface_match:
                current_iface = iface_match.group(1)
                continue

            sess_match = session_re.search(line)
            if sess_match:
                current_session = ServiceSession(
                    interface   = current_iface,
                    service_set = sess_match.group(1),
                    session_id  = int(sess_match.group(2)),
                    alg         = sess_match.group(3),
                    flags       = sess_match.group(4),
                    ip_action   = sess_match.group(5),
                    offload     = sess_match.group(6),
                    asymmetric  = sess_match.group(7),
                )
                result.sessions.append(current_session)
                continue

            flow_match = flow_re.search(line)
            if flow_match and current_session:
                current_session.flows.append(ServiceSessionFlow(
                    protocol  = flow_match.group(1),
                    src_ip    = flow_match.group(2),
                    src_port  = int(flow_match.group(3)),
                    dst_ip    = flow_match.group(4),
                    dst_port  = int(flow_match.group(5)),
                    direction = flow_match.group(6),
                    flow_dir  = flow_match.group(7),
                    packets   = int(flow_match.group(8)),
                ))

        result.total_sessions = len(result.sessions)
        return result.to_dict()
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
# ────────────────────────────────────────────────────────────────────────────
def parse_show_services_nat_pool_brief(text_content: str) -> Dict[str, Any]:
    cmd = "show services nat pool brief | no-more"
    try:
        result   = ShowServicesNatPoolBrief()
        current  = None

        # "Interface: ms-2/2/0, Service set: CUST-BOFA-FSX-UCAST"
        hdr_re   = re.compile(r'Interface:\s*(\S+),\s*Service set:\s*(\S+)')

        # "POOL-NAME  NAPT-44  10.x.x.x-10.x.x.x  1024-65535  2"
        # port_range and ports_used are optional (DNAT pools omit them)
        pool_re  = re.compile(
            r'^(\S+)\s+(NAPT-\d+|DNAT-\d+|STATIC)\s+'
            r'([\d.]+-[\d.]+)'
            r'(?:\s+([\d]+-[\d]+))?'
            r'(?:\s+(\d+))?'
        )

        for line in text_content.splitlines():
            hdr_match = hdr_re.search(line)
            if hdr_match:
                current = NatPoolInterface(
                    interface   = hdr_match.group(1),
                    service_set = hdr_match.group(2),
                )
                result.interfaces.append(current)
                continue

            if current is None:
                continue

            pool_match = pool_re.match(line.strip())
            if pool_match:
                current.pools.append(NatPoolEntry(
                    pool_name     = pool_match.group(1),
                    nat_type      = pool_match.group(2),
                    address_range = pool_match.group(3),
                    port_range    = pool_match.group(4) or "",
                    ports_used    = int(pool_match.group(5)) if pool_match.group(5) else None,
                ))

        return result.to_dict()
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
# ────────────────────────────────────────────────────────────────────────────
def parse_show_services_service_sets_cpu_usage(text_content: str) -> Dict[str, Any]:
    cmd = "show services service-sets cpu-usage | no-more"
    try:
        result = ShowServicesServiceSetsCpuUsage()

        # "ms-2/2/0    CUST-BOFA-FSX-UCAST    0.00 %"
        row_re = re.compile(
            r'^(ms-\S+)\s+(\S+)\s+([\d.]+)\s*%',
            re.MULTILINE
        )

        for match in row_re.finditer(text_content):
            result.entries.append(ServiceSetCpuEntry(
                interface       = match.group(1),
                service_set     = match.group(2),
                cpu_utilization = float(match.group(3)),
            ))

        return result.to_dict()
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
# ────────────────────────────────────────────────────────────────────────────
def parse_show_services_service_sets_memory_usage(text_content: str) -> Dict[str, Any]:
    cmd = "show services service-sets memory-usage | no-more"
    try:
        result = ShowServicesServiceSetsMemoryUsage()

        # "ms-2/2/0    system    1553079792"
        row_re = re.compile(
            r'^(ms-\S+)\s+(\S+)\s+(\d+)',
            re.MULTILINE
        )

        for match in row_re.finditer(text_content):
            result.entries.append(ServiceSetMemoryEntry(
                interface   = match.group(1),
                service_set = match.group(2),
                bytes_used  = int(match.group(3)),
            ))

        return result.to_dict()
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
# ────────────────────────────────────────────────────────────────────────────
def parse_show_services_service_sets_summary(text_content: str) -> Dict[str, Any]:

    cmd = "show services service-sets summary | no-more"
    try:
        result = ShowServicesServiceSetsSummary()

        # "ms-2/2/0   4  1553115152  (13.45%)  3565120 ( 0.33%)  1.42 %"
        row_re = re.compile(
            r'^(ms-\S+)\s+'
            r'(\d+)\s+'
            r'(\d+)\s+\(\s*([\d.]+)%\)\s+'
            r'(\d+)\s+\(\s*([\d.]+)%\)\s+'
            r'([\d.]+)\s*%',
            re.MULTILINE
        )

        for match in row_re.finditer(text_content):
            result.entries.append(ServiceSetSummaryEntry(
                interface               = match.group(1),
                service_sets_configured = int(match.group(2)),
                bytes_used              = int(match.group(3)),
                bytes_used_pct          = float(match.group(4)),
                policy_bytes_used       = int(match.group(5)),
                policy_bytes_used_pct   = float(match.group(6)),
                cpu_utilization         = float(match.group(7)),
            ))

        return result.to_dict()
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
def parse_show_services_flows_brief(text_content: str) -> Dict[str, Any]:
    cmd = "show services flows brief | no-more"
    try:
        result = ShowServicesFlowsBrief()
        s = (text_content or "").strip()

        # device produces no output for this command — return empty structure
        if not s:
            return result.to_dict()

        for line in s.splitlines():
            line = line.strip()
            if not line or line.startswith("Flow") or line.startswith("---"):
                continue
            parts = line.split()
            if len(parts) >= 10:
                result.flows.append(
                    ShowServicesFlowsBriefEntry(
                        flow_id     = parts[0],
                        interface   = parts[1],
                        service_set = parts[2],
                        direction   = parts[3],
                        protocol    = parts[4],
                        src_address = parts[5],
                        dst_address = parts[6],
                        src_port    = parts[7],
                        dst_port    = parts[8],
                        packets     = int(parts[9])  if parts[9].isdigit()  else 0,
                        bytes       = int(parts[10]) if len(parts) > 10 and parts[10].isdigit() else 0,
                    )
                )

        result.total_flows = len(result.flows)
        return result.to_dict()

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
def parse_show_chassis_alarms(text_content: str) -> Dict[str, Any]:
    cmd = "show chassis alarms | no-more"
    try:
        result = ShowChassisAlarms()
        s = (text_content or "").strip()

        # no alarms or empty output
        if not s or re.search(r'no alarms currently active', s, re.IGNORECASE):
            return result.to_dict()

        # alarm count line: "2 alarms currently active"
        count_m = re.search(r'(\d+)\s+alarm', s, re.IGNORECASE)
        if count_m:
            result.alarm_count = int(count_m.group(1))

        # each alarm line: "2026-03-19 09:22:07 UTC  Major  Host 1 fxp0 : Ethernet Link Down"
        alarm_re = re.compile(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\S+)\s+'
            r'(Major|Minor|Warning)\s+'
            r'(.+)',
            re.IGNORECASE,
        )
        for m in alarm_re.finditer(s):
            result.alarms.append(
                AlarmEntry(
                    alarm_time  = m.group(1).strip(),
                    alarm_class = m.group(2).strip(),
                    description = m.group(3).strip(),
                )
            )

        return result.to_dict()

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
# ────────────────────────────────────────────────────────────────────────────────
def parse_show_system_alarms(text_content: str) -> Dict[str, Any]:
    cmd = "show system alarms | no-more"
    try:
        result = ShowSystemAlarms()
        s = (text_content or "").strip()

        # no alarms or empty output
        if not s or re.search(r'no alarms currently active', s, re.IGNORECASE):
            return result.to_dict()

        # alarm count line
        count_m = re.search(r'(\d+)\s+alarm', s, re.IGNORECASE)
        if count_m:
            result.alarm_count = int(count_m.group(1))

        # each alarm line
        alarm_re = re.compile(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\S+)\s+'
            r'(Major|Minor|Warning)\s+'
            r'(.+)',
            re.IGNORECASE,
        )
        for m in alarm_re.finditer(s):
            result.alarms.append(
                AlarmEntry(
                    alarm_time  = m.group(1).strip(),
                    alarm_class = m.group(2).strip(),
                    description = m.group(3).strip(),
                )
            )

        return result.to_dict()

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
# ────────────────────────────────────────────────────────────────────────────────
def parse_show_oam_cfm_interfaces(text_content: str) -> Dict[str, Any]:
    cmd = "show oam ethernet connectivity-fault-management interfaces extensive | no-more"
    try:
        result = ShowOamCfmInterfaces()
        s = (text_content or "").strip()

        # subsystem not running — return empty structure with flag set
        if re.search(r'subsystem not running', s, re.IGNORECASE):
            result.subsystem_not_running = True
            return result.to_dict()

        if not s:
            return result.to_dict()

        for block in re.split(r'\n(?=Interface name:)', s):
            if not block.strip() or 'Interface name:' not in block:
                continue

            intf_match = re.search(
                r'Interface name:\s+(\S+)\s*,\s*Interface status:\s+(\w+)\s*,\s*Link status:\s+(\w+)',
                block,
            )
            if not intf_match:
                continue

            iface = OamCfmInterface(
                interface_name   = intf_match.group(1),
                interface_status = intf_match.group(2),
                link_status      = intf_match.group(3),
            )

            md_m = re.search(
                r'Maintenance domain name:\s+(.+?)\s*,\s*Format:\s+(\w+)\s*,\s*Level:\s+(\d+)\s*,\s*MD Index:\s+(\d+)',
                block,
            )
            if md_m:
                iface.maintenance_domain_name = md_m.group(1).strip()
                iface.md_format               = md_m.group(2)
                iface.md_level                = int(md_m.group(3))
                iface.md_index                = int(md_m.group(4))

            ma_m = re.search(
                r'Maintenance association name:\s+(.+?)\s*,\s*Format:\s+(\w+)\s*,\s*MA Index:\s+(\d+)',
                block,
            )
            if ma_m:
                iface.maintenance_association_name = ma_m.group(1).strip()
                iface.ma_format                    = ma_m.group(2)
                iface.ma_index                     = int(ma_m.group(3))

            cc_m = re.search(
                r'Continuity-check status:\s+(\w+)\s*,\s*Interval:\s+(\S+)\s*,\s*Loss-threshold:\s+(.+)',
                block,
            )
            if cc_m:
                iface.continuity_check_status = cc_m.group(1)
                iface.cc_interval             = cc_m.group(2)
                iface.loss_threshold          = cc_m.group(3).strip()

            mep_m = re.search(
                r'MEP identifier:\s+(\d+)\s*,\s*Direction:\s+(\w+)\s*,\s*MAC address:\s+([0-9a-fA-F:]+)',
                block,
            )
            if mep_m:
                iface.mep_identifier = int(mep_m.group(1))
                iface.mep_direction  = mep_m.group(2)
                iface.mac_address    = mep_m.group(3)

            mep_status_m = re.search(r'MEP status:\s+(\w+)', block)
            if mep_status_m:
                iface.mep_status = mep_status_m.group(1)

            result.interfaces.append(iface)

        return result.to_dict()

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
