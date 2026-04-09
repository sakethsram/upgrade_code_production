from typing import List, Dict, Any
import re
import sys
import json
from datetime import datetime
from dataclasses import dataclass, asdict, field
import logging
import os
from lib.utilities import *
from models.cisco.cisco_asr9910 import *


logger = logging.getLogger(__name__)

def show_redundancy(content: str) -> List[Dict[str, Any]]:
    try:
        cmd = "show redundancy"

        if not content:
            raise ValueError(f"No output found for command: {cmd}")

        # "Node 0/RSP0/CPU0 is in ACTIVE role"
        active_match = re.search(r'Node\s+(\S+)\s+is in ACTIVE role', content)

        # "Partner node (0/RSP1/CPU0) is in STANDBY role"
        standby_match = re.search(r'Partner node\s+\((\S+)\)\s+is in STANDBY role', content)

        # "Last switch-over Tue Mar  3 09:09:09 2026: 1 day, 20 hours..."
        last_sw_match = re.search(r'Last switch-over\s+(.+?):\s+\d+\s+day', content)

        result = asdict(ShowRedundancy(
            ActiveNode=active_match.group(1).strip() if active_match else "",
            StandbyNode=standby_match.group(1).strip() if standby_match else "",
            RedundancyState="ACTIVE/STANDBY" if active_match and standby_match else "",
            RedundancyMode="",   # not present in XR show redundancy output
            LastSwitchover=last_sw_match.group(1).strip() if last_sw_match else ""
        ))

        return result

    except Exception as e:
        return [{"error": f"Error parsing command output: {str(e)}"}]


def show_install_active_summary(text_content):
    """
    Docstring for show_install_active_summary
    
    :param folder_path: Includes that output of show_install_active_summary
    :type folder_path: str
    :return: Json string of show_install_active_summary.txt file
    :rtype: Dict[str, Any]
    """
    cmd = "show install active summary"
    try: 

        result = {}
        match = re.search(
            r'Active Packages:\s*(?P<count>\d+)', 
        text_content
        )
        activePackages = int(match.group("count")) if match else 0
        
        label_match = re.search(
            r'^\s*Label\s*:\s*(?P<label>.+?)\s*$', 
        text_content,
            re.MULTILINE
        )
        label = label_match.group("label") if label_match else "unknown"

        package = re.findall(
            r'^\s+(?!Active)(?!Label)(\S+)',
        text_content,
            re.MULTILINE
        )

        packages = [line.strip() for line in package  if line.strip() ]

        result = asdict(
            ShowInstallActiveSummary(
                Label = label,
                AcivePackages = activePackages, 
                Packages=packages
            )
        )

        if not result: 
            return {"info": "No Active summary found"}

        return result
    
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_isis_adjacency(text_content) -> List[Dict[str, Any]]:
    cmd = "show isis adjacency"
    try:
        result = {}
        
        adj_re = re.compile(
            r'^(?P<systemID>\S+)\s+'
            r'(?P<interface>\S+)\s+'
            r'(?P<SNPA>\S+)\s+'
            r'(?P<state>\S+)\s+'
            r'(?P<hold>\d+)\s+'
            r'(?P<changed>not\s+up|\S+)\s+'   
            r'(?P<NSF>\S+)\s+'
            r'(?P<ipv4BFD>\S+)\s+'
            r'(?P<ipv6BFD>\S+)'
        )

        if not text_content:
            raise ValueError(f"No output found for command: {cmd}")

        current_level: int | None = None
        current_adjacencies: List[Dict] = []

        for line in text_content.splitlines():
            line = line.strip()
            if(
              not line or
              line.startswith("No IS-IS")
            ):
             continue
            #  correctly when the output contains both Level-1 and Level-2.
            level_match = re.match(
                r'^IS-IS\s+COLT\s+Level-(?P<lvl>\d+)\s+adjacencies:', line
            )
            if level_match:
                # Flush the previous section (if any) before starting the new one
                if current_level is not None:
                    result.append({
                        "totalAdjacency": 0,
                        "ISISColtAdjacencyLevel": current_level,
                        "adjacencies": current_adjacencies
                    })
                current_level = int(level_match.group("lvl"))
                current_adjacencies = []
                continue

            # Skip column-header and blank lines
            if not line or line.startswith("System") or line.startswith("BFD"):
                continue

            total_match = re.match(
                r'^Total\s+adjacency\s+count:\s*(?P<count>\d+)', line
            )
            if total_match:
                result.append({
                    "totalAdjacency": int(total_match.group("count")),
                    "ISISColtAdjacencyLevel": current_level,
                    "adjacencies": current_adjacencies
                })
                current_level = None
                current_adjacencies = []
                continue

            m = adj_re.match(line)
            if m:
                entry = ISISAdjacencies(
                    systemID=m.group("systemID"),
                    interface=m.group("interface"),
                    SNPA=m.group("SNPA"),
                    state=m.group("state"),
                    hold=m.group("hold"),
                    changed=m.group("changed"),
                    NSF=m.group("NSF"),
                    ipv4BFD=m.group("ipv4BFD"),
                    ipv6BFD=m.group("ipv6BFD"),
                )
                current_adjacencies.append(asdict(entry))

        # Edge-case: output ends without a "Total adjacency count" line
        if current_level is not None:
            result = {
                "totalAdjacency": 0,
                "ISISColtAdjacencyLevel": current_level,
                "adjacencies": current_adjacencies
            }

        if not result: 
            return {"info": "ISIS Adjancencies not Found"}

        return  result
    
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}


def show_bfd_session(text_content):
    """
    Parse 'show bfd session' output.

    Fixes applied:
      - The BFD table has THREE lines per session (not two):
          Line 1: interface, dest, echo, async, state
          Line 2: (blank / whitespace only)
          Line 3: continuation with hw and npu values
        The original regex tried to match hw/npu on the immediate next line,
        so it never matched the actual output format.
      - Interface regex now uses [A-Za-z][A-Za-z0-9]* to correctly capture
        names like BE1, TenGigE0/0/0/1, Bundle-Ether1, etc. including
        hyphenated names.
      - echo/async accept 'n/a' or the normal interval*mult pattern.
      - hw/npu on the continuation line accept 'n/a' or any non-space token.
    """
    cmd = "show bfd session"
    try:
        result = []

        bfd_pattern = re.compile(
            r'(?m)'
            # Interface: starts with letter, then letters/digits/hyphens,
            # optionally followed by /digit segments
            r'^(?P<interface>[A-Za-z][A-Za-z0-9\-]*(?:/\d+)*(?:\.\d+)?)\s+'
            # Destination IPv4
            r'(?P<destAddr>\d+\.\d+\.\d+\.\d+)\s+'
            # Echo: n/a  OR  value(unit*mult)
            r'(?P<echo>n/a|\S+\(\S+\*\d+\))\s+'
            # Async: n/a  OR  value(unit*mult)
            r'(?P<async_val>n/a|\S+\(\S+\*\d+\))\s+'
            # State
            r'(?P<state>\S+)\s*\n'
            # Skip one or more lines that do NOT start with a letter (blank/whitespace lines)
            r'(?:(?![A-Za-z]).*\n)*'
            # Continuation line: optional leading whitespace, then hw and npu
            # Both can be n/a or any non-space token
            r'\s+(?P<hw>\S+)\s+(?P<npu>\S+)'
        )

        for match in bfd_pattern.finditer(text_content):
            entry = ShowbfdSession(
                interface=match.group("interface"),
                destAddr=match.group("destAddr"),
                localDettime=[{
                    "echo": match.group("echo"),
                    "async": match.group("async_val")
                }],
                hw=match.group("hw"),
                npu=match.group("npu"),
                state=match.group("state")
            )
            result.append(asdict(entry))

        if not result:
            return {"info": "No BFD Session Found"}

        return {
            "totalCount": len(result),
            "bfd_session": result
        }

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_route_summary(text_content): 
    """
    Docstring for show_route_summary
    
    :param folder_path: Description
    :type folder_path: str
    """
    cmd = "show route summary"
    try: 
        result = {}

        print(" show route summary ...")
        
        route_summary = []

        pattern = re.compile(
            r'^(?P<routeSource>[A-Za-z0-9 _:-]+?)\s+'
            r'(?P<routes>\d+)\s+'
            r'(?P<backup>\d+)\s+'
            r'(?P<deleted>\d+)\s+'
            r'(?P<memory>\d+)',
            re.MULTILINE
        )

        for line in pattern.finditer(text_content): 
            
            mem = line.group('memory')
            memory = " ".join([mem, "bytes"])
            entry = ShowRouteSummary(
                routeSource=line.group('routeSource'),
                routes=int(line.group('routes')),
                backup=int(line.group('backup')),
                deleted=int(line.group('deleted')), 
                memory=memory
            )

            route_summary.append(asdict(entry))
        total_count = len(route_summary)

        result = {
            "totalCount": total_count, 
            "route_summary": route_summary
        }

        if not result: 
            return {"info": "No route summary found"}

        return result
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_bgp_all_summary(text_content):
    """
    Parse 'show bgp all summary' output and include:
      - per-AF NeighborCount
      - overall totalNeighborCount

    Notes:
      - Regex for neighbor IPv4 is used in code via raw strings (no backslash warnings).
    """
    cmd = "show bgp all summary"
    try:

        if "not active" in text_content: 
            return {
                "BGP instance": "default", 
                "Status": "not active"
            }

        af_blocks = re.split(r'(?=^\s*Address Family:\s+)', text_content, flags=re.MULTILINE)
        af_blocks = [b.strip() for b in af_blocks if b.strip()]

        af_results = []
        overall_neighbor_count = 0

        for block in af_blocks:

            # AF Name
            af_match = re.search(r'^Address Family:\s+(.+)', block, flags=re.MULTILINE)
            af_name = af_match.group(1).strip() if af_match else "UNKNOWN"

            # Global fields
            rid  = re.search(r'router identifier\s+(\S+)', block)
            las  = re.search(r'local AS number\s+(\d+)', block)
            tsta = re.search(r'BGP table state:\s+(\S+)', block)
            mver = re.search(r'main routing table version\s+(\d+)', block)

            # Process table
            proc_re = re.compile(
                r'^(?P<proc>\S+)\s+'
                r'(?P<rcv>\d+)\s+'
                r'(?P<brib>\d+)\s+'
                r'(?P<label>\d+)\s+'
                r'(?P<import>\d+)\s+'
                r'(?P<send>\d+)\s+'
                r'(?P<standby>\d+)$',
                re.MULTILINE
            )

            process_versions = [
                BgpProcessVersion(
                    Process=m.group("proc"),
                    RcvTblVer=m.group("rcv"),
                    BRibRib=m.group("brib"),
                    LabelVer=m.group("label"),
                    ImportVer=m.group("import"),
                    SendTblVer=m.group("send"),
                    StandbyVer=m.group("standby")
                )
                for m in proc_re.finditer(block)
            ]

            # Neighbor table
            neighbors = []
            inside = False

            for line in block.splitlines():
                s = line.strip()

                if s.lower().startswith("neighbor"):
                    inside = True
                    continue

                if inside and s.startswith("Address Family:"):
                    break

                if inside and s:
                    cols = re.split(r'\s+', s)

                    # Neighbor must start with IPv4
                    # Example pattern: r'^\d{1,3}(\.\d{1,3}){3}$'
                    if len(cols) >= 10 and re.match(r'^\d{1,3}(?:\.\d{1,3}){3}$', cols[0]):
                        neighbors.append(
                            BgpNeighbor(
                                Neighbor=cols[0],
                                Spk=cols[1],
                                RemoteAS=cols[2],
                                MsgRcvd=cols[3],
                                MsgSent=cols[4],
                                TblVer=cols[5],
                                InQ=cols[6],
                                OutQ=cols[7],
                                UpDown=cols[8],
                                StatePfxRcd=cols[9]
                            )
                        )

            neighbor_count = len(neighbors)
            overall_neighbor_count += neighbor_count

            af_results.append(asdict(
                ShowBgpAllAllSummaryAF(
                    AF=af_name,
                    RouterID=rid.group(1) if rid else "",
                    LocalAS=las.group(1) if las else "",
                    TableState=tsta.group(1) if tsta else "",
                    MainTableVersion=mver.group(1) if mver else "",
                    ProcessVersions=process_versions,
                    Neighbors=neighbors,
                    NeighborCount=neighbor_count   # ensure dataclass allows this (see fix above)
                )
            ))

        if not af_results: 
            return {"info": "% BGP instance 'default' not active"}

        wrapped = {
            "totalCount": len(af_results),                # number of AF blocks
            "totalNeighborCount": overall_neighbor_count, # sum across AFs
            "addressFamilies": af_results
        }

        return wrapped
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}



def show_bgp_vrf_all_summary(text_content) -> Dict[str, Any]:
    cmd = "show bgp vrf all summary"
    try:

        if "not active" in text_content: 
            return {
                "BGP instance": "default", 
                "Status": "not active"
            }

        blocks = re.split(r'(?=^VRF:\s+)', text_content, flags=re.MULTILINE)
        blocks = [b.strip() for b in blocks if b.strip()]

        vrf_results = []

        for block in blocks:

            # ------------------ BASIC VRF INFO ------------------
            vrf_name  = re.search(r'^VRF:\s+(\S+)', block, flags=re.MULTILINE)
            vrf_state = re.search(r'^BGP VRF \S+,\s*state:\s+(\S+)', block, flags=re.MULTILINE)
            rd        = re.search(r'^BGP Route Distinguisher:\s+(\S+)', block, flags=re.MULTILINE)
            vrfid     = re.search(r'^VRF ID:\s+(\S+)', block, flags=re.MULTILINE)
            rid_as    = re.search(r'BGP router identifier\s+(\S+),\s*local AS number\s+(\d+)', block)
            tstate    = re.search(r'^BGP table state:\s+(\S+)', block, flags=re.MULTILINE)
            main_ver  = re.search(r'^BGP main routing table version\s+(\d+)', block, flags=re.MULTILINE)

            # ------------------ PROCESS TABLE ------------------
            proc_re = re.compile(
                r'^(?P<proc>\S+)\s+'
                r'(?P<rcv>\d+)\s+'
                r'(?P<brib>\d+)\s+'
                r'(?P<label>\d+)\s+'
                r'(?P<import>\d+)\s+'
                r'(?P<send>\d+)\s+'
                r'(?P<standby>\d+)$',
                re.MULTILINE
            )

            process_list = [
                {
                    "Process":  m.group("proc"),
                    "RcvTblVer": m.group("rcv"),
                    "BRibRib":   m.group("brib"),
                    "LabelVer":  m.group("label"),
                    "ImportVer": m.group("import"),
                    "SendTblVer":m.group("send"),
                    "StandbyVer":m.group("standby")
                }
                for m in proc_re.finditer(block)
            ]

            # ------------------ NEIGHBOR TABLE ------------------
            neighbors = []
            lines = block.splitlines()

            inside_neighbor_section = False

            for idx, line in enumerate(lines):
                line_strip = line.strip()

                # Header line: start collecting neighbors
                if re.match(r'^Neighbor\s+Spk\s+AS', line_strip):
                    inside_neighbor_section = True
                    continue

                # Stop at next VRF:
                if inside_neighbor_section and line_strip.startswith("VRF:"):
                    break

                # Stop at completely blank line after neighbors
                if inside_neighbor_section and line_strip == "":
                    # continue reading until repeated blank or next VRF
                    continue

                if inside_neighbor_section:
                    cols = re.split(r'\s+', line_strip)
                    if len(cols) >= 10 and re.match(r'\d{1,3}\.', cols[0]):  # neighbor IP must look like IPv4
                        neighbors.append(
                            {
                                "Neighbor": cols[0],
                                "Speaker": cols[1],
                                "AS": cols[2],
                                "MsgRcvd": cols[3],
                                "MsgSent": cols[4],
                                "TblVer": cols[5],
                                "InQ": cols[6],
                                "OutQ": cols[7],
                                "UpDown": cols[8],
                                "StPfxRcd": cols[9],
                            }
                        )

            # ------------------ CREATE VRF ENTRY ------------------
            vrf_results.append({
                "VRF": vrf_name.group(1) if vrf_name else "",
                "VRFState": vrf_state.group(1) if vrf_state else "",
                "RouteDistinguisher": rd.group(1) if rd else "",
                "VRFID": vrfid.group(1) if vrfid else "",
                "RouterID": rid_as.group(1) if rid_as else "",
                "LocalAS": rid_as.group(2) if rid_as else "",
                "TableState": tstate.group(1) if tstate else "",
                "MainTableVersion": main_ver.group(1) if main_ver else "",
                "ProcessVersions": process_list,
                "Neighbors": neighbors
            })

        if not vrf_results: 
            return {"info": "BGP VRF Summary not found"}
        # ------------------ WRAP WITH TOTAL COUNT ------------------
        wrapped = {
            "totalCount": len(vrf_results),
            "vrfs": vrf_results
        }

        return wrapped

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
        
def show_mpls_ldp_neighbor(text_content) -> List[Dict[str, Any]]:
    """
    Parse 'show mpls ldp neighbor' output for ASR9910 (multiple neighbors).
    """
    cmd = "show mpls ldp neighbor"
    try:
        def uniq(seq):
            seen = set()
            out = []
            for x in seq:
                if x not in seen:
                    seen.add(x)
                    out.append(x)
            return out

        # Split into neighbor blocks starting at each "Peer LDP Identifier:"
        blocks = re.split(r'(?=^Peer LDP Identifier:\s)', text_content, flags=re.MULTILINE)
        blocks = [b.strip() for b in blocks if b.strip()]

        results: List[Dict[str, Any]] = []

        for b in blocks:
            # --- Peer identifier ---
            peer_id_m = re.search(r'^Peer LDP Identifier:\s+(\S+)', b, flags=re.MULTILINE)
            peer_id = peer_id_m.group(1) if peer_id_m else ""

            # --- TCP connection line ---
            tcp_line_m = re.search(r'^\s*TCP connection:\s+(.+)$', b, flags=re.MULTILINE)
            md5 = "off"
            remote_tcp = ""
            local_tcp = ""
            if tcp_line_m:
                tcp_line = tcp_line_m.group(1).strip()
                if "MD5 on" in tcp_line:
                    md5 = "on"
                tcp_line_clean = tcp_line.split(";")[0].strip()
                ep_m = re.match(r'(\S+)\s*-\s*(\S+)', tcp_line_clean)
                if ep_m:
                    remote_tcp = ep_m.group(1).strip()  # peer endpoint
                    local_tcp  = ep_m.group(2).strip()  # local endpoint

            # --- Graceful Restart ---
            gr_m = re.search(r'Graceful Restart:\s+(Yes|No)', b)
            graceful_restart = gr_m.group(1) if gr_m else "No"


            # --- State / Msgs / Mode ---
            state_m = re.search(r'^\s*State:\s*([A-Za-z]+).*$', b, flags=re.MULTILINE)
            session_state = state_m.group(1) if state_m else ""

            msgs_m = re.search(r'Msgs\s+sent/rcvd:\s+(\d+)/(\d+)', b)
            msgs_sent = msgs_m.group(1) if msgs_m else ""
            msgs_recv = msgs_m.group(2) if msgs_m else ""

            # Label distribution mode is typically at the end of the same line as State
            mode_m = re.search(
                r'^\s*State:.*?Msgs sent/rcvd:\s*\d+/\d+;\s*([A-Za-z-]+)\s*$',
                b, flags=re.MULTILINE
            )
            label_mode = mode_m.group(1) if mode_m else ""

            # --- Uptime ---
            up_m = re.search(r'Up time:\s+(\S+)', b)
            uptime = up_m.group(1) if up_m else ""

            # --- Discovery Interfaces: IPv4 ---
            disc_ipv4: List[str] = []
            disc_ipv6: List[str] = []

            disc_block_m = re.search(r'LDP Discovery Sources:(?P<body>.*?)(?:^Addresses bound to this peer:|\Z)', 
                                     b, flags=re.DOTALL | re.MULTILINE)
            if disc_block_m:
                disc_body = disc_block_m.group('body')

                # IPv4 block
                ipv4_body_m = re.search(r'IPv4:\s*\(\d+\)\s*(?P<body>.*?)(?:^\s*IPv6:|\Z)', 
                                        disc_body, flags=re.DOTALL | re.MULTILINE)
                if ipv4_body_m:
                    ipv4_body = ipv4_body_m.group('body')
                    disc_ipv4 = re.findall(r'^\s+(\S+)\s*$', ipv4_body, flags=re.MULTILINE)

                # IPv6 block
                ipv6_body_m = re.search(r'IPv6:\s*\(\d+\)\s*(?P<body>.*?)(?:^\S|\Z)', 
                                        disc_body, flags=re.DOTALL | re.MULTILINE)
                if ipv6_body_m:
                    ipv6_body = ipv6_body_m.group('body')
                    # Interfaces may be listed one per line similar to IPv4
                    disc_ipv6 = re.findall(r'^\s+(\S+)\s*$', ipv6_body, flags=re.MULTILINE)

            disc_ipv4 = uniq(disc_ipv4)
            disc_ipv6 = uniq(disc_ipv6)

            # --- Bound Addresses: IPv4 & IPv6 ---
            bound_ipv4: List[str] = []
            bound_ipv6: List[str] = []

            addr_block_m = re.search(r'Addresses bound to this peer:(?P<body>.*)\Z', 
                                     b, flags=re.DOTALL | re.MULTILINE)
            if addr_block_m:
                addr_body = addr_block_m.group('body')

                # IPv4 addresses section only
                ipv4_addrs_m = re.search(r'IPv4:\s*\(\d+\)\s*(?P<body>.*?)(?:^\s*IPv6:|\Z)', 
                                         addr_body, flags=re.DOTALL | re.MULTILINE)
                if ipv4_addrs_m:
                    ipv4_addrs_body = ipv4_addrs_m.group('body')
                    bound_ipv4 = re.findall(r'\b\d{1,3}(?:\.\d{1,3}){3}\b', ipv4_addrs_body)

                # IPv6 addresses section only (full IPv6 patterns can be complex; accept tokens with ':')
                ipv6_addrs_m = re.search(r'IPv6:\s*\(\d+\)\s*(?P<body>.*?)(?:^\S|\Z)', 
                                         addr_body, flags=re.DOTALL | re.MULTILINE)
                if ipv6_addrs_m:
                    ipv6_addrs_body = ipv6_addrs_m.group('body')
                    # Match simple IPv6 tokens (hex + colons); skip trailing artifacts
                    bound_ipv6 = re.findall(r'\b[0-9A-Fa-f:]+:[0-9A-Fa-f:]+\b', ipv6_addrs_body)

            bound_ipv4 = uniq(bound_ipv4)
            bound_ipv6 = uniq(bound_ipv6)

            entry = ShowMplsLdpNeighbor(
                PeerLdpIdentifier=peer_id,
                RemoteTCP=remote_tcp,
                LocalTCP=local_tcp,
                MD5=md5,
                GracefulRestart=graceful_restart,
                SessionState=session_state,
                LabelDistributionMode=label_mode,
                Uptime=uptime,
                MsgsSent=msgs_sent,
                MsgsReceived=msgs_recv,
                DiscoveryInterfacesIPv4=disc_ipv4,
                DiscoveryInterfacesIPv6=disc_ipv6,
                BoundIPv4Addresses=bound_ipv4,
                BoundIPv6Addresses=bound_ipv6
            )

            results.append(asdict(entry))

        if not results: 
            return {"info": "MPLS LDP neighbor not found"}

        # === Wrap like your other commands ===
        wrapped = {
            "totalCount": len(results),
            "mpls_ldp_neighbor": results
        }

        return wrapped

    except Exception as e:
        return {"error": f"Error reading/parsing output: {str(e)}"}


def show_pim_neighbor(text_content) -> Dict[str, Any]:
    """
    Parse 'show pim neighbor' into a list wrapped with totalCount.

    Fix applied:
      - Function parameter was named 'content' in the original but the body
        referenced 'text_content' (NameError). Standardised to 'text_content'
        throughout to match the project convention used by all other parsers.
    """
    cmd = "show pim neighbor"
    try:
        # Extract VRF name from the header line, e.g. "PIM neighbors in VRF default"
        vrf_match = re.search(r'PIM neighbors in VRF\s+(\S+)', text_content, re.IGNORECASE)
        vrf = vrf_match.group(1) if vrf_match else "default"

        header_skip_prefixes = (
            "pim neighbors in vrf",
            "flag:",
            "* indicates the neighbor",
            "neighbor address",
            "---",
        )
        rows: List[str] = []
        buffer = ""

        for raw_line in text_content.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue

            lower = stripped.lower()
            if lower.startswith(header_skip_prefixes):
                continue

            # New row starts with IPv4 token with optional trailing '*'
            first_token = stripped.split()[0]
            if re.match(r'^\d{1,3}(?:\.\d{1,3}){3}\*?$', first_token):
                if buffer:
                    rows.append(buffer.strip())
                buffer = stripped
            else:
                if buffer:
                    buffer += " " + stripped
                else:
                    continue

        if buffer:
            rows.append(buffer.strip())

        row_re = re.compile(
            r'^\s*'
            r'(?P<iptoken>\d{1,3}(?:\.\d{1,3}){3}\*?)'
            r'\s+'
            r'(?P<intf>\S+)'
            r'\s+'
            r'(?P<uptime>\S+)'
            r'\s+'
            r'(?P<expires>\S+)'
            r'\s+'
            r'(?P<drpri>\d+)'
            r'\s+'
            r'(?P<flags>.+?)'
            r'\s*$'
        )

        parsed: List[Dict[str, Any]] = []

        for r in rows:
            m = row_re.match(r)
            if not m:
                continue

            iptoken = m.group("iptoken")
            neighbor_addr = iptoken
            is_self = iptoken.endswith('*')

            intf    = m.group("intf")
            uptime  = m.group("uptime")
            expires = m.group("expires")

            try:
                drpri = int(m.group("drpri"))
            except Exception:
                drpri = 0

            flags_raw = m.group("flags").strip()
            is_dr = "(dr)" in flags_raw.lower()

            letters: List[str] = []
            for token in flags_raw.replace("(", " ").replace(")", " ").split():
                t = token.strip()
                if t in ("B", "E", "P", "S") and t not in letters:
                    letters.append(t)

            entry = PimNeighbor(
                neighborAddress=neighbor_addr,
                isSelf=is_self,
                interface=intf,
                uptime=uptime,
                expires=expires,
                drPriority=drpri,
                isDR=is_dr,
                flags=letters,
                flagsRaw=flags_raw,
                vrf=vrf,
            )
            parsed.append(asdict(entry))

        if not parsed:
            return {"info": "PIM neighbor not found"}

        return {
            "totalCount": len(parsed),
            "pim_neighbor": parsed
        }

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}


def show_pfm_location_all(text_content) -> Dict[str, Any]:
    """
    Parse 'show pfm location all' output.

    Fix applied:
      - The body referenced the variable 'content' instead of the parameter
        'text_content', causing a NameError. Replaced all occurrences of
        'content' with 'text_content' inside the function body.
    """
    cmd = "show pfm location all"
    try:
        results: List[Dict[str, Any]] = []

        # Split blocks at node headers  ← was: re.split(..., content)
        blocks = re.split(r'(?m)^\s*node:\s+', text_content)[1:]

        row_re = re.compile(
            r'(?m)^(?P<raised>[^|\r\n]+)\|'
            r'(?P<snum>[^|]+)\|'
            r'(?P<fname>[^|]+)\|'
            r'(?P<sev>[^|]+)\|'
            r'(?P<pid>[^|]+)\|'
            r'(?P<dev>[^|]+)\|'
            r'(?P<handle>0x[0-9A-Fa-f]+)\s*$'
        )

        def grab(pat: str, text: str, default: str = None) -> str:
            m = re.search(pat, text, flags=re.MULTILINE)
            return m.group(1).strip() if m else default

        for block in blocks:
            lines = block.splitlines()
            if not lines:
                continue

            node_name = lines[0].strip()

            current_time = grab(r'^CURRENT TIME:\s+(.+)$', block, "None")
            pfm_total_s  = grab(r'PFM TOTAL:\s+(\d+)', block, "0")
            ea_s         = grab(r'EMERGENCY/ALERT\(E/A\):\s+(\d+)', block, "0")
            cr_s         = grab(r'CRITICAL\(CR\):\s+(\d+)', block, "0")
            er_s         = grab(r'ERROR\(ER\):\s+(\d+)', block, "0")

            pfm_total = int(pfm_total_s) if pfm_total_s is not None else 0
            ea        = int(ea_s)        if ea_s        is not None else 0
            cr        = int(cr_s)        if cr_s        is not None else 0
            er        = int(er_s)        if er_s        is not None else 0

            data_row = None
            for m in row_re.finditer(block):
                data_row = m
                break

            if data_row:
                raised = data_row.group("raised").strip()
                snum   = data_row.group("snum").strip()
                fname  = data_row.group("fname").strip()
                sev    = data_row.group("sev").strip()
                pid    = data_row.group("pid").strip()
                dev    = data_row.group("dev").strip()
                handle = data_row.group("handle").strip()

                sev = sev.upper() if sev else "NO"

                if snum == "--" or snum.strip() == "":
                    snum = "None"
            else:
                raised = "None"
                snum   = "None"
                fname  = "None"
                sev    = "NO"
                pid    = "None"
                dev    = "None"
                handle = "None"

            results.append(asdict(
                ShowPfmLocationAll(
                    Node=node_name,
                    CurrentTime=current_time,
                    PFMTotal=pfm_total,
                    EmergencyAlert=ea,
                    Critical=cr,
                    Error=er,
                    RaisedTime=raised,
                    SNumber=snum,
                    FaultName=fname,
                    Severity=sev,
                    ProcessID=pid,
                    DevicePath=dev,
                    Handle=handle
                )
            ))

        if not results:
            return {"info": "PFM location not found"}

        return {
            "totalCount": len(results),
            "pfm_location_all": results
        }

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_watchdog_memory_state(text_content): 
    """
    Docstring for show_watchdog_memory_state
    
    :param folder_path: Description
    """
    cmd = "show watchdog memory-state location all"
    try: 
        
        result = {}
        nodeName = None
        pattern = re.compile(
            r"----\s*(?P<section>[^-]+?)\s*----\s*"
            r"Memory information:\s*"
            r"\s*Physical Memory\s*:\s*(\b(?P<phymem>\d+(?:\.\d+)?)\s*(?P<phyunit>MB|KB|GB)\b)\s*"
            r"\s*Free Memory\s*:\s*(\b(?P<freemem>\d+(?:\.\d+)?)\s*(?P<freeunit>MB|KB|GB)\b)\s*"
            r"\s*Memory State\s*:\s*(?P<state>\w+)", 
            re.MULTILINE
        )
        matches = pattern.finditer(text_content)

        for match in matches: 
            physicalMem = " ".join([match.group("phymem"), match.group("phyunit")])
            freeMem = " ".join([match.group('freemem'), match.group('freeunit')])

            mem_info = memoryInfo(
                physicalMem=physicalMem, 
                freeMem=freeMem, 
                memoryState=match.group("state")
            )
            nodeName = match.group("section").strip()
            node_state = ShowWatchdogMemoryState(
                nodeName=nodeName,
                memoryInfo=[mem_info]
            )

            result[nodeName] = asdict(node_state)
        
        if not result: 
            return {"info": "No watchdog memroy state found"}

        return result
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}



def show_interface_description(text_content):
    cmd = "show interface description"
    try:
        interfaceDes = []
        result = {}

        for line in text_content.splitlines():
            line = line.strip()

            if (
                not line
                or line.startswith("Interface")
                or line.startswith("-")
                or line.endswith("UTC")
            ):
                continue

            cols = re.split(r'\s{2,}', line)

            entry = ShowInterfaceDescription(
                    interface = cols[0],
                    status = cols[1],
                    protocol = cols[2],
                    description = cols[3] if len(cols) > 3 else None
            )

            interfaceDes.append(asdict(entry))
        result = {
            "totalInterfaces": len(interfaceDes), 
            "interfaces": interfaceDes
        }

        if not result: 
            return {"info": "No interface description found"}
          
        return result
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}

    

def show_filesystem(text_content) -> Dict[str, Any]:
    cmd = "show filesystem"
    try:

        result: List[Dict[str, Any]] = []

        for raw_line in text_content.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            lower = line.lower()

            # Skip headers
            if (
                lower.startswith("file systems:")
                or lower.startswith("size(b)")
                or lower.startswith("file systems")
                or lower.startswith("---")
            ):
                continue

            # Expect 5+ columns split by 2+ spaces
            cols = re.split(r'\s{2,}', line)

            if len(cols) < 5:
                continue

            size_str, free_str, fs_type, flags, prefixes_raw = cols[:5]

            # Numeric parsing
            try:
                size_bytes = int(size_str.replace(",", ""))
                free_bytes = int(free_str.replace(",", ""))
            except ValueError:
                continue

            # Clean prefix list (avoid duplicates)
            prefixes = sorted(set([p.strip() for p in prefixes_raw.split() if p.strip()]))

            entry = {
                "sizeBytes": size_bytes,
                "freeBytes": free_bytes,
                "fsType": fs_type,
                "flags": flags,
                "prefixes": prefixes
            }

            result.append(entry)
        if not result: 
            return {"info": "show filesystem output not found"}

        # Final output wrapper
        wrapped = {
            "totalCount": len(result),
            "filesystem": result
        }

        return wrapped

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_l2vpn_xconnect_brief(text_content) -> Dict[str, Any]:
    """
    Parse 'show l2vpn xconnect brief' EVPN summary for ASR9910.
    """
    cmd = "show l2vpn xconnect brief"
    try:
        WS = r'(?:[ \t\u00A0]|&nbsp;)+'

        # --------- Aggregate ALL PW‑Ether rows ----------
        pw_line_re = re.compile(rf'(?im)^\s*PW-?Ether\b(?P<rest>[^\r\n]*)$')
        pw_up_sum = pw_down_sum = pw_unr_sum = 0

        for m in pw_line_re.finditer(text_content):
            rest = m.group("rest")
            # First three integers after 'PW-Ether' on that line
            nums = re.findall(r'\d+', rest)
            if len(nums) >= 3:
                up, down, unr = map(int, nums[:3])
                pw_up_sum   += up
                pw_down_sum += down
                pw_unr_sum  += unr

        # --------- Find LAST 'Total' occurrence (summary or row style) ----------
        total_up = total_down = total_unr = None
        pos_summary = pos_row = -1

        # Summary style: "Total: X UP, Y DOWN, Z UNRESOLVED"
        total_summary_re = re.compile(
            rf'(?im)\bTotal:{WS}'
            rf'(?P<up>\d+){WS}UP,{WS}'
            rf'(?P<down>\d+){WS}DOWN,{WS}'
            rf'(?P<unr>\d+){WS}UNRESOLVED\b'
        )
        last_summary = None
        for tm in total_summary_re.finditer(text_content):
            last_summary = tm
        if last_summary:
            total_up = int(last_summary.group("up"))
            total_down = int(last_summary.group("down"))
            total_unr = int(last_summary.group("unr"))
            pos_summary = last_summary.end()

        # Row style: "Total  X  Y  Z"
        total_row_re = re.compile(
            rf'(?im)\bTotal\b{WS}(?P<up>\d+){WS}(?P<down>\d+){WS}(?P<unr>\d+)\b'
        )
        last_row = None
        for tr in total_row_re.finditer(text_content):
            last_row = tr
        if last_row:
            pos_row = last_row.end()

        # Prefer whichever 'Total' appears last in the text
        if pos_row > pos_summary and last_row:
            total_up = int(last_row.group("up"))
            total_down = int(last_row.group("down"))
            total_unr = int(last_row.group("unr"))

        # --------- Build JSON in the requested shape ----------
        evpn_vpms_obj: Dict[str, Any] = {
            "PwEther": {
                "UP": pw_up_sum,
                "DOWN": pw_down_sum,
                "UNRESOLVED": pw_unr_sum
            }
        }

        # Only include Total if we parsed it
        if total_up is not None and total_down is not None and total_unr is not None:
            evpn_vpms_obj["Total"] = {
                "UP": total_up,
                "DOWN": total_down,
                "UNRESOLVED": total_unr
            }

        if not evpn_vpms_obj: 
            return {"info": "L2VPN xconnect Brief not found"}

        result = { "EVPN VPMS": evpn_vpms_obj }
        
        return result

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}


def show_platform(text_content): 
    """
    Docstring for show_platform
    
    :param folder_path:  Includes that output of show platform
    :type folder_path: str
    :return: Return the JSON file of the show_platform.txt
    :rtype: Dict[str, Any]
    """
    cmd = "show platform"
    try: 
        platform=[]
        result = {}

        pattern = re.compile(
            r'^(?P<node>\d+\S+)\s+'
            r'(?P<type>\S(?:.*?\S)?)\s+'
            r'(?P<state>IOS XR RUN|OPERATIONAL|UP)\s*'
            r'(?P<configstate>\S+)?\s*$',
            re.MULTILINE
        )

        for line in pattern.finditer(text_content): 
            try:
                config_state = line.group('configstate')
                if line.group('configstate') is None:
                    config_state = ""

                entry = ShowPlatform(
                    Node=line.group('node'), 
                    Type=line.group('type'), 
                    State=line.group('state'), 
                    ConfigState=config_state
                )
                platform.append(asdict(entry))
            except Exception as per_row_err: 
                print(f"error parsing a row: {per_row_err}")
                sys.exit(1)

        total_count = len(platform)
        result = {
            "totalCount": total_count, 
            "platformInfo": platform
        }

        if not result: 
            return {"info": "No platform details found" }

        return result
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}


def show_hw_module_fpd(text_content): 
    """
    Docstring for show_hw_module_fpd
    
    :param folder_path: Description
    :type folder_path: str
    """
    cmd = "show hw-module fpd"
    try: 
        result = {}

        auto_upgrade_pattern = re.search(
            r'^Auto-upgrade\s*:\s*(?P<AutoUpgrade>\S+)',
            text_content,
            re.MULTILINE
        )

        auto_upgrade = auto_upgrade_pattern.group("AutoUpgrade") if auto_upgrade_pattern else ""
        fpds = []
        WS = r'(?:[ \t\u00A0]|&nbsp;)+'

        line_re = re.compile(
            rf'^(?P<Location>\S+){WS}'
            rf'(?P<CardType>\S+){WS}'
            rf'(?P<HWver>\S+){WS}'
            rf'(?P<FPDdevice>\S+){WS}'
            rf'(?P<ATRstatus>.*?){WS}'
            rf'(?P<Running>\d+(?:\.\d+)?){WS}'
            rf'(?P<Programd>\d+(?:\.\d+)?)\s*$',
            re.MULTILINE
        )

        for line in line_re.finditer(text_content): 
            atr_status = line.group("ATRstatus")

            try: 
                running = float(line.group("Running"))
            except ValueError: 
                running = None 
                sys.exit(1)
            
            try: 
                programd = float(line.group("Programd"))
            except ValueError: 
                programd = None 
                sys.exit(1)
            
            fpd_version = {
                "Running": running, 
                "Programd": programd
            }

            fpd = FPDEntry( 
                Location=line.group("Location"), 
                CardType=line.group("CardType"), 
                HWver=line.group("HWver"), 
                FPDdevice=line.group("FPDdevice"), 
                ATRstatus=atr_status, 
                FPDVersions=fpd_version
            )

            fpds.append(asdict(fpd))
        fpdsCount = len(fpds)
        
        result = {
            "FPDsCount": fpdsCount,
            "AutoUpgrade": auto_upgrade, 
            "FPDs": fpds
        }

        if not result: 
            return {"info": "No hw-module fpd details found"}

        return result
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}



def show_interfaces(text_content):
    cmd = "show interfaces"
    try:

        results = {}

        # Split Bundle-Ether blocks
        bundle_blocks = re.split(
            r'(?=^Bundle-Ether\S+\s+is\s+)',
            text_content,
            flags=re.MULTILINE
        )

        for block in bundle_blocks:
            if not block.strip():
                continue

            try:
                # Header
                header_match = re.search(
                    r'^(?P<Interface>Bundle-Ether\S+)\s+is\s+'
                    r'(?P<AdminState>\S+),\s+line\s+protocol\s+is\s+'
                    r'(?P<LineProtocol>\S+)',
                    block,
                    flags=re.MULTILINE | re.IGNORECASE
                )

                # MAC
                mac_match = re.search(r'address\s+is\s+([0-9A-Fa-f\.\:-]+)', block)

                # Description
                desc_match = re.search(
                    r'^\s*Description:\s+(.+)$',
                    block,
                    flags=re.MULTILINE
                )

                # IP address
                ip_match = re.search(
                    r'^\s*Internet address is\s+(\S+)$',
                    block,
                    flags=re.MULTILINE
                )

                # MTU + Bandwidth
                mtu_bw_match = re.search(
                    r'^\s*MTU\s+(\d+)\s+bytes,\s+BW\s+(\d+)\s+Kbit',
                    block,
                    flags=re.MULTILINE
                )

                # Last flapped
                flap_match = re.search(
                    r'^\s*Last link flapped\s+(.+)$',
                    block,
                    flags=re.MULTILINE
                )
                arp_match = re.search(
                    r'ARP\s+timeout\s+([0-9:]+)',
                    block,
                    flags=re.IGNORECASE
                )

                # Member count
                member_count_match = re.search(
                    r'^\s*No\. of members in this bundle:\s+(\d+)',
                    block,
                    flags=re.MULTILINE
                )

                # Member interfaces
                member_pattern = re.findall(
                    r'^\s*(HundredGigE\S+)\s+'
                    r'(Full-duplex|Half-duplex)\s+'
                    r'(\S+)\s+'
                    r'(\S+)\s*$',
                    block,
                    flags=re.MULTILINE
                )

                members: List[Dict[str, Any]] = []
                for m in member_pattern:
                    members.append({
                        "Interface": m[0],
                        "Duplex": m[1],
                        "Speed": m[2],
                        "State": m[3]
                    })

                entry = InterfaceEntry(
                    Interface=header_match.group("Interface") if header_match else "",
                    AdminState=header_match.group("AdminState") if header_match else "",
                    LineProtocol=header_match.group("LineProtocol") if header_match else "",
                    MacAddress=mac_match.group(1) if mac_match else "",
                    Description=(desc_match.group(1).strip() if desc_match else ""),
                    InternetAddress=(ip_match.group(1) if ip_match else ""),
                    MTU=(mtu_bw_match.group(1) if mtu_bw_match else ""),
                    Bandwidth=(mtu_bw_match.group(2) if mtu_bw_match else ""),
                    LastLinkFlapped=(flap_match.group(1).strip() if flap_match else ""),
                    ArpTimeout=(arp_match.group(1) if arp_match else ""),   # <-- FIXED
                    MemberCount=int(member_count_match.group(1)) if member_count_match else 0,
                    Members=[InterfaceMember(**m) for m in members]
                )

                results = asdict(entry)

            except Exception as inner_error:
                print(f"Error parsing block: {inner_error}")
                continue

        return results
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return {"error": f"Error parsing {cmd}: {str(e)}"}



def show_msdp_peer(text_content) -> Dict[str, Any]:

    """
    Abstract parser for 'show msdp peer'.
    - If output contains 'Peer not found' (any case), returns empty peers with totalCount=0.
    - If peers are present (future enhancement), this function is the place to add parsing logic.
    - Wraps output as: [ { "totalCount": <int>, "msdp_peers": [ ... ] } ]
    """
    cmd = "show msdp peer"
    try:

        # Normalize whitespace minimally for robust checks
        text = text_content.strip()

        # Case 1: No peers at all
        if re.search(r'\bpeer\s+not\s+found\b', text, flags=re.IGNORECASE):
            peers: List[Dict[str, Any]] = []
            wrapped = {
                "totalCount": len(peers),
                "msdp_peers": peers
            }

            return wrapped

        # For now, if it's not "Peer not found" and no parser implemented, return empty with a note
        wrapped = {
            "totalCount": 0,
            "msdp_peers": []
        }

        return wrapped

    except Exception as e:
        return {"error": f"Error parsing show msdp peer: {str(e)}"} 
    
def show_proc_cpu(text_content): 
    """
    Docstring for show_proc_cpu
    
    :param folder_path: Description
    :type folder_path: str
    :return: Description
    :rtype: Dict[str, Any]
    """
    cmd = "show process cpu"
    try: 
        
        result = {}

        utilization_pattern = re.compile(
            r"CPU utilization for one minute:\s*(?P<one_min>\d+%)\s*;\s*five minutes:\s*(?P<five_min>\d+%)\s*;\s*fifteen minutes:\s*(?P<fifteen_min>\d+%)"
        )

        utilization = utilization_pattern.search(text_content)
        print(f"Utilization: {utilization}")

        entry = ShowProcessCPU(
            oneMinUtilization=utilization.group("one_min"), 
            fifteenMinUtilization=utilization.group("five_min"), 
            fiveMinUtilization=utilization.group("fifteen_min")
        )

        result = asdict(entry)

        if not result: 
            return {"info": "Process CPU details not found"}
          
        return result
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}


def show_media(text_content): 
    """
    Docstring for show_media
    
    :param folder_path: Description
    :type folder_path: str
    """
    cmd = "show media"
    try: 

        result = {}        
        mediaInfo = []

        mediaLocation = re.search(
            r'^Media Info for Location:\s*([A-Za-z0-9_-]+)$',
            text_content, 
            re.MULTILINE
        )
        location = mediaLocation.group(1) if mediaLocation else ""

        # WS = r'(?:[ \t\u00A0]|&nbsp;)+'
        pattern = re.compile(
            rf'^(?P<partition>\S+):?\s+'
            rf'(?P<size>\S+)\s+'
            rf'(?P<used>\S+)\s+'
            rf'(?P<percent>\S+)\s+'
            rf'(?P<avail>\S+)$', 
            re.MULTILINE
        )

        for line in pattern.finditer(text_content): 

            if line.group('partition') == "Media" or line.group('partition') == "Partition":
                continue

            entry = MediaInfo( 
                Partition=line.group('partition'), 
                Size=line.group('size'),
                Used=line.group('used'),
                Percent=line.group('percent'),
                Avail=line.group('avail')
            )
            mediaInfo.append(asdict(entry))
        
        result = {
            "TotalCount": len(mediaInfo),
            "MediaLoc": location, 
            "MediaInfo": mediaInfo
        }

        if not result: 
            return {"info": "No media details found"}
        
        return result
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}



def show_asr_version(text_content):
    """
    Parse 'show version' output for IOS-XR.
    """
    cmd = "show version"
    try:
        if not text_content:
            return {"info": "No data found for show version"}

        # Handles both "Version : 7.5.2" and "Version      : 7.5.2"
        version_pattern = re.compile(
            r"Version\s*:\s*(?P<version>\d+\.\d+\.\d+)"
        )

        # Handles singular and plural time units; trailing spaces fine
        uptime_pattern = re.compile(
            r"System uptime is\s*(?P<uptime>(?:\d+\s+(?:weeks?|days?|hours?|minutes?|seconds?)\s*)+)"
        )

        # Skips "cisco IOS" line; stops before whitespace/parens after model token
        model_pattern = re.compile(
            r"^cisco\s+(?P<model>(?!IOS\b)[A-Za-z0-9]+)",
            re.IGNORECASE | re.MULTILINE
        )
        version_match = version_pattern.search(text_content)
        uptime_match  = uptime_pattern.search(text_content)
        model_match   = model_pattern.search(text_content)

        if not version_match:
            return {"error": "Version not found in output"}
        if not uptime_match:
            return {"error": "System uptime not found in output"}

        model = model_match.group("model").upper() if model_match else "unknown"

        entry = ShowVersion(
            version=version_match.group("version"),
            model=model,
            systemUptime=uptime_match.group("uptime").strip()
        )
        return asdict(entry)

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}

