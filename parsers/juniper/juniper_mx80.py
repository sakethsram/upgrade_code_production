# import os
# import re
# import sys
# import json
# from dataclasses import dataclass, field, asdict
# from typing import List, Dict, Any, Optional, Union
# from models.junos.junos_mx80 import *
# from lib.utilities import *

# def parse_show_arp_no_resolve() -> dict[str, any]:
#     """Parse 'show arp no-resolve | no-more' output"""
#     cmd = "show arp no-resolve | no-more"
#     text_content = COMMAND_OUTPUT_STORE.get(cmd).get("output")
    
#     print(text_content)    
#     result = ShowArpNoResolve()
#     pattern = r'([0-9a-f:]{17})\s+(\d+\.\d+\.\d+\.\d+)\s+(\S+)\s+(\S+)'
#     for match in re.finditer(pattern, text_content, re.IGNORECASE):
#         entry = ShowArpNoResolveEntry(
#             mac_address=match.group(1),
#             ip_address=match.group(2),
#             interface=match.group(3),
#             flags=match.group(4)
#         )
#         result.entries.append(entry)
    
#     total_match = re.search(r'Total entries:\s*(\d+)', text_content)
#     result.total_entries = int(total_match.group(1)) if total_match else len(result.entries)
    
#     result = asdict(result)
#      # Creating json file 
#     output_file = write_json(
#         command_name="show_arp",
#         vendor="juniper",
#         model="mx80",
#         json_data=result,
#         json_file_path="precheck_jsons/"
#     )
#     return output_file

# # def parse_show_vrrp_summary(folder_path: str) -> dict[str, any]:
# #     """Parse 'show vrrp summary | no-more' output"""
# #     cmd = "show vrrp summary | no-more"
# #     raw_output = COMMAND_OUTPUT_STORE.get(cmd)
# #     print(raw_output)
# #     vrrp_result = ShowVrrpSummary()

# #     # Regex for main VRRP entry line
# #     header_pattern = re.compile(
# #         r'^(?P<interface>\S+)\s+'
# #         r'(?P<state>\S+)\s+'
# #         r'(?P<group>\d+)\s+'
# #         r'(?P<vr_state>\S+)\s+'
# #         r'(?P<vr_mode>\S+)\s+'
# #         r'(?P<addr_type>lcl|vip)\s+'
# #         r'(?P<address>\d+\.\d+\.\d+\.\d+)',
# #         re.IGNORECASE | re.MULTILINE
# #     )

# #     # Regex for continuation address lines (vip/lcl only)
# #     continuation_pattern = re.compile(
# #         r'^\s+(?P<addr_type>lcl|vip)\s+'
# #         r'(?P<address>\d+\.\d+\.\d+\.\d+)',
# #         re.IGNORECASE | re.MULTILINE
# #     )

# #     current_entry = None

# #     for line in raw_output.splitlines():
# #         header_match = header_pattern.match(line)
# #         if header_match:
# #             current_entry = ShowVrrpSummaryEntry(
# #                 interface=header_match.group("interface"),
# #                 state=header_match.group("state"),
# #                 group=int(header_match.group("group")),
# #                 vr_state=header_match.group("vr_state"),
# #                 vr_mode=header_match.group("vr_mode"),
# #                 addresses=[]
# #             )

# #             addr_obj = ShowVrrpSummaryAddress(
# #                 type=header_match.group("addr_type"),
# #                 address=header_match.group("address")
# #             )
# #             current_entry.addresses.append(addr_obj)
# #             vrrp_result.entries.append(current_entry)
# #             continue

# #         cont_match = continuation_pattern.match(line)
# #         if cont_match and current_entry:
# #             addr_obj = ShowVrrpSummaryAddress(
# #                 type=cont_match.group("addr_type"),
# #                 address=cont_match.group("address")
# #             )
# #             current_entry.addresses.append(addr_obj)

# #     return vrrp_result.to_dict()
# # def parse_show_lldp_neighbors(folder_path: str) -> dict[str, any]:
# #     """Parse 'show lldp neighbors | no-more' output"""
# #     cmd = "show lldp neighbors | no-more"
# #     text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #     print(text_content)
# #     result = ShowLldpNeighbors()
    
# #     pattern = r'^(\S+)\s+(\S+)\s+([0-9a-f:]{17})\s+(\S+)\s+(.+)$'
# #     for match in re.finditer(pattern, text_content, re.MULTILINE):
# #         entry = ShowLldpNeighborsEntry(
# #             local_interface=match.group(1),
# #             parent_interface=match.group(2),
# #             chassis_id=match.group(3),
# #             port_info=match.group(4),
# #             system_name=match.group(5).strip()
# #         )
# #         result.entries.append(entry)
    
# #     return asdict(result)
# # def parse_show_bfd_session(folder_path: str) -> dict[str, any]:
# #     """Parse 'show bfd session | no-more' output"""
# #     cmd = "show bfd session | no-more"
# #     text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #     print(text_content)    
# #     result = ShowBfdSession()
    
# #     pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\S+)\s+(\S+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)'
# #     for match in re.finditer(pattern, text_content):
# #         entry = ShowBfdSessionEntry(
# #             address=match.group(1),
# #             state=match.group(2),
# #             interface=match.group(3),
# #             detect_time=match.group(4),
# #             transmit_interval=match.group(5),
# #             multiplier=match.group(6)
# #         )
# #         result.entries.append(entry)
    
# #     summary_match = re.search(r'(\d+)\s+sessions?,\s+(\d+)\s+clients?', text_content)
# #     if summary_match:
# #         result.total_sessions = int(summary_match.group(1))
# #         result.total_clients = int(summary_match.group(2))
    
# #     return asdict(result)
# # def parse_show_rsvp_neighbor(folder_path: str) -> dict[str, any]:
# #     """Parse show rsvp neighbor no more output"""
# #     try:
# #         cmd = "show rsvp neighbor no more"
# #         text_content = COMMAND_OUTPUT_STORE.get(cmd)
        
# #         print("\n", text_content, "\n")
# #         result = ShowRsvpNeighbor()

# #         # Extract total neighbors
# #         total_match = re.search(r"RSVP neighbor:\s+(\d+)\s+learned", text_content)
# #         if total_match:
# #             result.total_neighbors = int(total_match.group(1))

# #         # Split each line and parse fields by position
# #         lines = text_content.split('\n')
# #         for line in lines:
# #             # Skip header and empty lines
# #             if 'Address' in line or not line.strip() or 'RSVP neighbor' in line:
# #                 continue
            
# #             # Split by whitespace and filter out empty strings
# #             fields = line.split()
            
# #             # We need at least 8 fields: Address, Idle, Up/Dn, Date, Time, HelloInt, HelloTx/Rx, MsgRcvd
# #             if len(fields) >= 8:
# #                 try:
# #                     entry = ShowRsvpNeighborEntry(
# #                         address=fields[0],
# #                         idle=int(fields[1]),
# #                         up_dn=fields[2],
# #                         last_change=f"{fields[3]} {fields[4]}",  # Combine date and time
# #                         hello_interval=int(fields[5]),
# #                         hello_tx_rx=fields[6],
# #                         msg_rcvd=int(fields[7])
# #                     )
# #                     result.entries.append(entry)
# #                 except (ValueError, IndexError) as e:
# #                     # Skip lines that don't match expected format
# #                     continue
        
# #         result_dict = asdict(result)  # FIXED: Create result_dict first
# #         print(result_dict)  # Then print it
# #         return result_dict
        
# #     except FileNotFoundError:
# #         return {"error": f"File not found: {folder_path}/show_rsvp_neighbor_no-more.txt"}
# #     except Exception as e:
# #         return {"error": f"Error reading file: {str(e)}"}
# # def parse_show_rsvp_session(folder_path: str) -> Dict[str, Any]:

# #     """Parse 'show rsvp session | no-more' output"""
# #     try:
# #         cmd = "show rsvp session | no-more"
# #         text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #         print(text_content)
# #         result = ShowRsvpSession()
        
# #         # Parse Ingress RSVP section
# #         ingress_header = re.search(r'Ingress RSVP:\s+(\d+)\s+sessions', text_content)
# #         if ingress_header:
# #             result.ingress_sessions = int(ingress_header.group(1))
        
# #         ingress_total = re.search(r'Total\s+(\d+)\s+displayed,\s+Up\s+(\d+),\s+Down\s+(\d+)', 
# #                                   text_content.split('Egress RSVP:')[0] if 'Egress RSVP:' in text_content else text_content)
# #         if ingress_total:
# #             result.ingress_up = int(ingress_total.group(2))
# #             result.ingress_down = int(ingress_total.group(3))
        
# #         # Pattern for Ingress entries
# #         ingress_pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+)$'
        
# #         # Extract ingress section
# #         if 'Ingress RSVP:' in text_content and 'Egress RSVP:' in text_content:
# #             ingress_section = text_content.split('Ingress RSVP:')[1].split('Egress RSVP:')[0]
# #             for match in re.finditer(ingress_pattern, ingress_section, re.MULTILINE):
# #                 entry = RsvpSessionIngressEntry(
# #                     to=match.group(1),
# #                     from_=match.group(2),
# #                     state=match.group(3),
# #                     rt=int(match.group(4)),
# #                     style=f"{match.group(5)} {match.group(6)}",
# #                     label_in=match.group(7),
# #                     label_out=match.group(8),
# #                     lsp_name=match.group(9).strip()
# #                 )
# #                 result.ingress_entries.append(entry)
        
# #         # Parse Egress RSVP section
# #         egress_header = re.search(r'Egress RSVP:\s+(\d+)\s+sessions', text_content)
# #         if egress_header:
# #             result.egress_sessions = int(egress_header.group(1))
        
# #         if 'Egress RSVP:' in text_content:
# #             egress_section_text = text_content.split('Egress RSVP:')[1]
# #             egress_total = re.search(r'Total\s+(\d+)\s+displayed,\s+Up\s+(\d+),\s+Down\s+(\d+)', 
# #                                      egress_section_text.split('Transit RSVP:')[0] if 'Transit RSVP:' in egress_section_text else egress_section_text)
# #             if egress_total:
# #                 result.egress_up = int(egress_total.group(2))
# #                 result.egress_down = int(egress_total.group(3))
        
# #         # Pattern for Egress entries
# #         egress_pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+)$'
        
# #         # Extract egress section
# #         if 'Egress RSVP:' in text_content:
# #             egress_section = text_content.split('Egress RSVP:')[1]
# #             if 'Transit RSVP:' in egress_section:
# #                 egress_section = egress_section.split('Transit RSVP:')[0]
            
# #             for match in re.finditer(egress_pattern, egress_section, re.MULTILINE):
# #                 entry = RsvpSessionEgressEntry(
# #                     to=match.group(1),
# #                     from_=match.group(2),
# #                     state=match.group(3),
# #                     rt=int(match.group(4)),
# #                     style=f"{match.group(5)} {match.group(6)}",
# #                     label_in=match.group(7),
# #                     label_out=match.group(8),
# #                     lsp_name=match.group(9).strip()
# #                 )
# #                 result.egress_entries.append(entry)
        
# #         # Parse Transit RSVP section
# #         transit_header = re.search(r'Transit RSVP:\s+(\d+)\s+sessions', text_content)
# #         if transit_header:
# #             result.transit_sessions = int(transit_header.group(1))
        
# #         # Pattern for Transit entries
# #         transit_pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+)$'
        
# #         # Extract transit section
# #         if 'Transit RSVP:' in text_content:
# #             transit_section = text_content.split('Transit RSVP:')[1]
            
# #             for match in re.finditer(transit_pattern, transit_section, re.MULTILINE):
# #                 entry = RsvpSessionTransitEntry(
# #                     to=match.group(1),
# #                     from_=match.group(2),
# #                     state=match.group(3),
# #                     rt=int(match.group(4)),
# #                     style=f"{match.group(5)} {match.group(6)}",
# #                     label_in=match.group(7),
# #                     label_out=match.group(8),
# #                     lsp_name=match.group(9).strip()
# #                 )
# #                 result.transit_entries.append(entry)
        
# #         # FIXED: Try to find Transit summary, if not found calculate from entries
# #         if 'Transit RSVP:' in text_content:
# #             transit_section_text = text_content.split('Transit RSVP:')[1]
# #             transit_total = re.search(r'Total\s+(\d+)\s+displayed,\s+Up\s+(\d+),\s+Down\s+(\d+)', transit_section_text)
# #             if transit_total:
# #                 result.transit_up = int(transit_total.group(2))
# #                 result.transit_down = int(transit_total.group(3))
# #             else:
# #                 # If no summary line, count entries by their state
# #                 result.transit_up = sum(1 for e in result.transit_entries if e.state == 'Up')
# #                 result.transit_down = sum(1 for e in result.transit_entries if e.state == 'Down')
        
# #         result_dict = asdict(result)
# #         # print(json.dumps(result_dict, indent=4))
# #         return result_dict
        
# #     except FileNotFoundError:
# #         return {"error": f"File not found: {folder_path}/show_rsvp_session_no-more.txt"}
# #     except Exception as e:
# #         return {"error": f"Error reading file: {str(e)}"}
# # def parse_show_route_table_inet0(folder_path: str) -> Dict[str, Any]:
# #     """Parse show route table inet.0 output"""
# #     try:
# #         cmd = "show route table inet.0"
# #         text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #         print(text_content)
        
# #         result = RouteTableData(
# #             table_name="",
# #             total_destinations=0,
# #             total_routes=0,
# #             active_routes=0,
# #             holddown_routes=0,
# #             hidden_routes=0,
# #             entries=[]
# #         )
        
# #         # Extract header information
# #         header_match = re.search(
# #             r'(inet\.0):\s+(\d+)\s+destinations,\s+(\d+)\s+routes\s+\((\d+)\s+active,\s+(\d+)\s+holddown,\s+(\d+)\s+hidden\)',
# #             text_content
# #         )
        
# #         if header_match:
# #             result.table_name = header_match.group(1)
# #             result.total_destinations = int(header_match.group(2))
# #             result.total_routes = int(header_match.group(3))
# #             result.active_routes = int(header_match.group(4))
# #             result.holddown_routes = int(header_match.group(5))
# #             result.hidden_routes = int(header_match.group(6))
        
# #         # Parse route entries
# #         lines = text_content.split('\n')
        
# #         i = 0
# #         while i < len(lines):
# #             line = lines[i].strip()
            
# #             # Skip empty lines and header lines
# #             if not line or line.startswith('+') or line.startswith('inet.'):
# #                 i += 1
# #                 continue
            
# #             # Match destination line with route info
# #             # Pattern handles both routes with and without metrics
# #             dest_match = re.match(
# #                 r'^([\d\.\/]+)\s+(\*?)(\[[\w\-]+\/\d+\])\s+([\w\d\s:]+?)(?:,\s+metric\s+(\d+))?$',
# #                 line
# #             )
            
# #             if dest_match:
# #                 destination = dest_match.group(1)
# #                 flags = dest_match.group(2)
# #                 protocol_pref = dest_match.group(3)
# #                 age = dest_match.group(4).strip()
# #                 metric = int(dest_match.group(5)) if dest_match.group(5) else 0
                
# #                 # Extract protocol and preference from [Protocol/Preference]
# #                 protocol_match = re.search(r'\[([\w\-]+)/(\d+)\]', protocol_pref)
# #                 protocol = protocol_match.group(1) if protocol_match else ""
# #                 preference = int(protocol_match.group(2)) if protocol_match else 0
                
# #                 # Look for next hop line (starts with ">")
# #                 next_hop = ""
# #                 interface = ""
                
# #                 # Check if there's a next line
# #                 if i + 1 < len(lines):
# #                     next_line = lines[i + 1].strip()
                    
# #                     if next_line.startswith('>'):
# #                         # Format: > to next_hop via interface
# #                         hop_match = re.search(r'>\s+to\s+([\d\.]+)\s+via\s+([\w\-\.\/]+)', next_line)
# #                         if hop_match:
# #                             next_hop = hop_match.group(1)
# #                             interface = hop_match.group(2)
# #                             i += 1  # Skip the next line since we processed it
# #                         else:
# #                             # Format: > via interface (for Direct routes)
# #                             hop_match2 = re.search(r'>\s+via\s+([\w\-\.\/]+)', next_line)
# #                             if hop_match2:
# #                                 interface = hop_match2.group(1)
# #                                 next_hop = ""
# #                                 i += 1
# #                     elif 'Local via' in next_line:
# #                         # Format: Local via interface
# #                         hop_match3 = re.search(r'Local\s+via\s+([\w\-\.\/]+)', next_line)
# #                         if hop_match3:
# #                             interface = hop_match3.group(1)
# #                             next_hop = "Local"
# #                             i += 1
                
# #                 entry = RouteEntry(
# #                     destination=destination,
# #                     protocol=protocol,
# #                     preference=preference,
# #                     metric=metric,
# #                     age=age,
# #                     next_hop=next_hop,
# #                     interface=interface,
# #                     flags=flags
# #                 )
# #                 result.entries.append(entry)
            
# #             i += 1
        
# #         result_dict = asdict(result)
# #         return result_dict
        
# #     except FileNotFoundError:
# #         return {"error": f"File not found: {folder_path}/show_route_table_inet0_no-more.txt"}
# #     except Exception as e:
# #         return {"error": f"Error reading file: {str(e)}"}
# # def parse_show_route_table_inet3(folder_path: str) -> dict:
# #     """Parse 'show route table inet.3 | no-more' output"""
# #     try:
# #         cmd = "show route table inet.3 | no-more"
# #         text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #         print(text_content)  
        
# #         result = ShowRouteTableInet3()
        
# #         # Extract header information
# #         header_match = re.search(
# #             r'inet\.3:\s+(\d+)\s+destinations,\s+(\d+)\s+routes\s+\((\d+)\s+active,\s+(\d+)\s+holddown,\s+(\d+)\s+hidden\)', 
# #             text_content
# #         )
# #         if header_match:
# #             result.total_destinations = int(header_match.group(1))
# #             result.total_routes = int(header_match.group(2))
# #             result.active_routes = int(header_match.group(3))
# #             result.holddown_routes = int(header_match.group(4))
# #             result.hidden_routes = int(header_match.group(5))
        
# #         lines = text_content.split('\n')
# #         i = 0
# #         current_entry = None
        
# #         while i < len(lines):
# #             line = lines[i]
            
# #             # Skip empty lines and header lines
# #             if not line.strip() or line.strip().startswith('+') or line.strip().startswith('inet.3:'):
# #                 i += 1
# #                 continue
            
# #             # Match route entry line: destination *[protocol/preference] age, metric value
# #             route_match = re.match(r'^(\S+)\s+\*\[(\S+)/(\d+)\]\s+(.+?),\s+metric\s+(\d+)', line)
# #             if route_match:
# #                 # Save previous entry if exists
# #                 if current_entry:
# #                     result.entries.append(current_entry)
                
# #                 # Create new entry
# #                 current_entry = ShowRouteTableInet3Entry(
# #                     destination=route_match.group(1),
# #                     protocol=route_match.group(2),
# #                     preference=route_match.group(3),
# #                     metric=route_match.group(5),
# #                     age=route_match.group(4)
# #                 )
# #             elif current_entry:
# #                 # Try to match next-hop lines
# #                 stripped_line = line.strip()
                
# #                 if stripped_line.startswith('>'):
# #                     # Primary next-hop (starts with >)
# #                     # Pattern: > to IP via interface[, Push label][, Push label(top)]
# #                     nexthop_match = re.match(
# #                         r'>\s+to\s+(\S+)\s+via\s+(\S+?)(?:,\s+Push\s+(\S+?))?(?:,\s+Push\s+(\S+?))?\s*$',
# #                         stripped_line
# #                     )
# #                     if nexthop_match:
# #                         to_addr = nexthop_match.group(1)
# #                         via_iface = nexthop_match.group(2).rstrip(',')
                        
# #                         # Build MPLS label string
# #                         mpls_label = ""
# #                         label1 = nexthop_match.group(3)
# #                         label2 = nexthop_match.group(4)
                        
# #                         if label1 and label2:
# #                             # Two labels (stacked)
# #                             # Remove "(top)" from label2 if present
# #                             label2_clean = label2.replace('(top)', '')
# #                             mpls_label = f"Push {label1}, Push {label2_clean}"
# #                         elif label1:
# #                             # Single label
# #                             mpls_label = f"Push {label1}"
                        
# #                         nexthop = ShowRouteTableInet3NextHop(
# #                             to=to_addr,
# #                             via=via_iface,
# #                             mpls_label=mpls_label
# #                         )
# #                         current_entry.next_hops.append(nexthop)
# #                 else:
# #                     # Secondary next-hop (no >)
# #                     # Pattern: to IP via interface[, Push label][, Push label(top)]
# #                     nexthop_match = re.match(
# #                         r'to\s+(\S+)\s+via\s+(\S+?)(?:,\s+Push\s+(\S+?))?(?:,\s+Push\s+(\S+?))?\s*$',
# #                         stripped_line
# #                     )
# #                     if nexthop_match:
# #                         to_addr = nexthop_match.group(1)
# #                         via_iface = nexthop_match.group(2).rstrip(',')
                        
# #                         # Build MPLS label string
# #                         mpls_label = ""
# #                         label1 = nexthop_match.group(3)
# #                         label2 = nexthop_match.group(4)
                        
# #                         if label1 and label2:
# #                             # Two labels (stacked)
# #                             label2_clean = label2.replace('(top)', '')
# #                             mpls_label = f"Push {label1}, Push {label2_clean}"
# #                         elif label1:
# #                             # Single label
# #                             mpls_label = f"Push {label1}"
                        
# #                         nexthop = ShowRouteTableInet3NextHop(
# #                             to=to_addr,
# #                             via=via_iface,
# #                             mpls_label=mpls_label
# #                         )
# #                         current_entry.next_hops.append(nexthop)
            
# #             i += 1
        
# #         # Don't forget the last entry
# #         if current_entry:
# #             result.entries.append(current_entry)
        
# #         return result.to_dict()
        
# #     except FileNotFoundError:
# #         return {"error": f"File not found: {folder_path}/show_route_table_inet3_no-more.txt"}
# #     except Exception as e:
# #         return {"error": f"Error reading file: {str(e)}"}
# # def parse_show_route_table_mpls0(folder_path: str) -> dict[str, any]:
# #     """Parse 'show route table mpls.0 | no-more' output"""
# #     cmd = "show route table mpls.0 | no-more"
# #     text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #     print(text_content)
# #     header_match = re.search(r'mpls\.0: (\d+) destinations, (\d+) routes \((\d+) active, (\d+) holddown, (\d+) hidden\)', text_content)
# #     if header_match:
# #         result.total_destinations = int(header_match.group(1))
# #         result.total_routes = int(header_match.group(2))
# #         result.active_routes = int(header_match.group(3))
# #         result.holddown_routes = int(header_match.group(4))
# #         result.hidden_routes = int(header_match.group(5))
    
# #     lines = text_content.split('\n')
# #     i = 0
# #     current_entry = None
    
# #     while i < len(lines):
# #         line = lines[i]
        
# #         # Match route entry line - metric is optional for VPN routes
# #         route_match = re.match(r'^(\d+(?:\(S=\d+\))?)\s+\*\[(\S+)/(\d+)\]\s+(.+?)(?:,\s+metric\s+(\d+))?$', line)
# #         if route_match:
# #             if current_entry:
# #                 result.entries.append(current_entry)
            
# #             current_entry = ShowRouteTableMpls0Entry(
# #                 label=route_match.group(1),
# #                 protocol=route_match.group(2),
# #                 preference=route_match.group(3),
# #                 metric=route_match.group(5) if route_match.group(5) else "",
# #                 age=route_match.group(4)
# #             )
# #         elif current_entry:
# #             # Parse next-hop lines
# #             # Match "to table X" format
# #             table_match = re.match(r'^\s+to table\s+(\S+)', line)
# #             if table_match:
# #                 nexthop = ShowRouteTableMpls0NextHop(
# #                     action="to table " + table_match.group(1)
# #                 )
# #                 current_entry.next_hops.append(nexthop)
            
# #             # Match "Receive" action
# #             elif re.match(r'^\s+Receive', line):
# #                 nexthop = ShowRouteTableMpls0NextHop(action="Receive")
# #                 current_entry.next_hops.append(nexthop)
            
# #             # Match "via lsi.X (LSP_NAME), Pop" format
# #             elif 'via lsi.' in line:
# #                 lsi_match = re.match(r'^\s+>\s+via\s+(lsi\.\d+)\s+\(([^)]+)\),\s+(\w+)', line)
# #                 if lsi_match:
# #                     nexthop = ShowRouteTableMpls0NextHop(
# #                         via=lsi_match.group(1),
# #                         lsp_name=lsi_match.group(2),
# #                         action=lsi_match.group(3)
# #                     )
# #                     current_entry.next_hops.append(nexthop)
            
# #             # Match "via vt-X, Pop" format (can start with > or just whitespace)
# #             elif 'via vt-' in line:
# #                 vt_match = re.match(r'^\s+>?\s*via\s+(vt-[\d/\.]+),\s+(\w+)', line)
# #                 if vt_match:
# #                     nexthop = ShowRouteTableMpls0NextHop(
# #                         via=vt_match.group(1),
# #                         action=vt_match.group(2)
# #                     )
# #                     current_entry.next_hops.append(nexthop)
            
# #             # Match "via ms-X, Pop" format
# #             elif 'via ms-' in line:
# #                 ms_match = re.match(r'^\s+>\s+via\s+(ms-[\d/\.]+),\s+(\w+)', line)
# #                 if ms_match:
# #                     nexthop = ShowRouteTableMpls0NextHop(
# #                         via=ms_match.group(1),
# #                         action=ms_match.group(2)
# #                     )
# #                     current_entry.next_hops.append(nexthop)
            
# #             # Match "to X via Y, [actions]" format
# #             elif line.strip().startswith('>') or line.strip().startswith('to '):
# #                 clean_line = line.strip().lstrip('>')
                
# #                 # First check for label-switched-path
# #                 lsp_match = re.search(r'label-switched-path\s+(.+?)$', clean_line)
# #                 lsp_name = lsp_match.group(1) if lsp_match else None
                
# #                 # Match the base next-hop format: to X via Y
# #                 nh_match = re.match(r'^\s*to\s+(\S+)\s+via\s+(\S+)', clean_line)
# #                 if nh_match:
# #                     to_addr = nh_match.group(1)
# #                     via_iface = nh_match.group(2).rstrip(',')  # Remove trailing comma
                    
# #                     # Extract everything after "via INTERFACE"
# #                     remainder = clean_line[nh_match.end():].strip()
                    
# #                     # Parse actions and labels from remainder
# #                     action = None
# #                     mpls_label = None
                    
# #                     if remainder:
# #                         # Remove comma if it's the first character
# #                         if remainder.startswith(','):
# #                             remainder = remainder[1:].strip()
                        
# #                         # Check for label-switched-path (already extracted above)
# #                         if 'label-switched-path' in remainder:
# #                             # No other action, just LSP
# #                             pass
# #                         elif remainder.startswith('Pop'):
# #                             action = "Pop"
# #                         elif remainder.startswith('Swap'):
# #                             # Handle "Swap X" or "Swap X, Push Y(top)"
# #                             swap_push_match = re.match(r'Swap\s+(\S+),\s+Push\s+(\S+)', remainder)
# #                             if swap_push_match:
# #                                 # Has both Swap and Push
# #                                 swap_label = swap_push_match.group(1).rstrip(',')
# #                                 push_label = swap_push_match.group(2)
# #                                 action = f"Swap {swap_label}, Push"
# #                                 mpls_label = push_label
# #                             else:
# #                                 # Just Swap
# #                                 swap_match = re.match(r'Swap\s+(\S+)', remainder)
# #                                 if swap_match:
# #                                     action = "Swap"
# #                                     mpls_label = swap_match.group(1).rstrip(',')
# #                         elif remainder.startswith('Push'):
# #                             push_match = re.match(r'Push\s+(\S+)', remainder)
# #                             if push_match:
# #                                 action = "Push"
# #                                 mpls_label = push_match.group(1)
                    
# #                     nexthop = ShowRouteTableMpls0NextHop(
# #                         to=to_addr,
# #                         via=via_iface,
# #                         action=action,
# #                         mpls_label=mpls_label,
# #                         lsp_name=lsp_name
# #                     )
# #                     current_entry.next_hops.append(nexthop)
        
# #         i += 1
    
# #     if current_entry:
# #         result.entries.append(current_entry)
    
# #     return asdict(result)
# # def parse_show_mpls_interface(folder_path: str) -> dict[str, any]:
# #     """Parse 'show mpls interface | no-more' output"""
# #     cmd = "show mpls interface | no-more"
# #     text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #     print(text_content,"\n","\n")
# #     result = ShowMplsInterface()
    
# #     pattern = r'^(\S+)\s+(Up|Down)\s+(.*)$'
# #     for match in re.finditer(pattern, text_content, re.MULTILINE):
# #         if match.group(1) == 'Interface':
# #             continue
# #         entry = ShowMplsInterfaceEntry(
# #             interface=match.group(1),
# #             state=match.group(2),
# #             administrative_groups=match.group(3).strip()
# #         )
# #         result.entries.append(entry)
    
# #     r=asdict(result)
# #     print(r)
# #     return r
# # def parse_show_mpls_lsp(folder_path: str) -> Dict[str, Any]:
# #        """Parse 'show mpls lsp | no-more' output"""
# #     try:
# #         cmd = "show mpls lsp | no-more"
# #         text_content = COMMAND_OUTPUT_STORE.get(cmd)
        
# #         print(text_content)
# #         result = ShowMplsLsp()
        
# #         # Parse Ingress LSP section
# #         ingress_header = re.search(r'Ingress LSP:\s+(\d+)\s+sessions', text_content)
# #         if ingress_header:
# #             result.ingress_sessions = int(ingress_header.group(1))
        
# #         ingress_total = re.search(r'Total\s+(\d+)\s+displayed,\s+Up\s+(\d+),\s+Down\s+(\d+)', 
# #                                   text_content.split('Egress LSP:')[0] if 'Egress LSP:' in text_content else text_content)
# #         if ingress_total:
# #             result.ingress_up = int(ingress_total.group(2))
# #             result.ingress_down = int(ingress_total.group(3))
        
# #         # FIXED: Corrected pattern for Ingress entries
# #         # The ActivePath column contains spaces (empty), and LSPname is at the end
# #         # Pattern: To From State Rt P <spaces for ActivePath> LSPname
# #         ingress_pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\w+)\s+(\d+)\s+(\*|\s+)\s+(.+)$'

# #         # Extract ingress section
# #         if 'Ingress LSP:' in text_content and 'Egress LSP:' in text_content:
# #             ingress_section = text_content.split('Ingress LSP:')[1].split('Egress LSP:')[0]
# #             for match in re.finditer(ingress_pattern, ingress_section, re.MULTILINE):
# #                 # Group 6 contains everything after the P field, which includes spaces and the LSP name
# #                 lsp_name_raw = match.group(6).strip()
                
# #                 entry = MplsLspIngressEntry(
# #                     to=match.group(1),
# #                     from_=match.group(2),
# #                     state=match.group(3),
# #                     rt=int(match.group(4)),
# #                     p=match.group(5).strip(),
# #                     active_path='',  # ActivePath is empty in this data
# #                     lsp_name=lsp_name_raw
# #                 )
# #                 result.ingress_entries.append(entry)
        
# #         # Parse Egress LSP section
# #         egress_header = re.search(r'Egress LSP:\s+(\d+)\s+sessions', text_content)
# #         if egress_header:
# #             result.egress_sessions = int(egress_header.group(1))
        
# #         if 'Egress LSP:' in text_content:
# #             egress_section_text = text_content.split('Egress LSP:')[1]
# #             egress_total = re.search(r'Total\s+(\d+)\s+displayed,\s+Up\s+(\d+),\s+Down\s+(\d+)', 
# #                                      egress_section_text.split('Transit LSP:')[0] if 'Transit LSP:' in egress_section_text else egress_section_text)
# #             if egress_total:
# #                 result.egress_up = int(egress_total.group(2))
# #                 result.egress_down = int(egress_total.group(3))
        
# #         # Pattern for Egress entries
# #         egress_pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+?)$'
        
# #         # Extract egress section
# #         if 'Egress LSP:' in text_content:
# #             egress_section = text_content.split('Egress LSP:')[1]
# #             if 'Transit LSP:' in egress_section:
# #                 egress_section = egress_section.split('Transit LSP:')[0]
            
# #             for match in re.finditer(egress_pattern, egress_section, re.MULTILINE):
# #                 entry = MplsLspEgressEntry(
# #                     to=match.group(1),
# #                     from_=match.group(2),
# #                     state=match.group(3),
# #                     rt=int(match.group(4)),
# #                     style=f"{match.group(5)} {match.group(6)}",
# #                     label_in=match.group(7),
# #                     label_out=match.group(8),
# #                     lsp_name=match.group(9).strip()
# #                 )
# #                 result.egress_entries.append(entry)
        
# #         # Parse Transit LSP section
# #         transit_header = re.search(r'Transit LSP:\s+(\d+)\s+sessions', text_content)
# #         if transit_header:
# #             result.transit_sessions = int(transit_header.group(1))
        
# #         # Pattern for Transit entries (same as Egress)
# #         transit_pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+?)$'
        
# #         # Extract transit section
# #         if 'Transit LSP:' in text_content:
# #             transit_section = text_content.split('Transit LSP:')[1]
            
# #             for match in re.finditer(transit_pattern, transit_section, re.MULTILINE):
# #                 entry = MplsLspTransitEntry(
# #                     to=match.group(1),
# #                     from_=match.group(2),
# #                     state=match.group(3),
# #                     rt=int(match.group(4)),
# #                     style=f"{match.group(5)} {match.group(6)}",
# #                     label_in=match.group(7),
# #                     label_out=match.group(8),
# #                     lsp_name=match.group(9).strip()
# #                 )
# #                 result.transit_entries.append(entry)
        
# #         # FIXED: Transit summary extraction (must be AFTER parsing entries)
# #         if 'Transit LSP:' in text_content:
# #             transit_section_text = text_content.split('Transit LSP:')[1]
# #             transit_total = re.search(r'Total\s+(\d+)\s+displayed,\s+Up\s+(\d+),\s+Down\s+(\d+)', transit_section_text)
# #             if transit_total:
# #                 result.transit_up = int(transit_total.group(2))
# #                 result.transit_down = int(transit_total.group(3))
# #             else:
# #                 # If no summary line, count entries by their state
# #                 result.transit_up = sum(1 for e in result.transit_entries if e.state == 'Up')
# #                 result.transit_down = sum(1 for e in result.transit_entries if e.state == 'Down')
        
# #         result_dict = asdict(result)
# #         #print(result_dict)
# #         return result_dict
        
# #     except FileNotFoundError:
# #         return {"error": f"File not found: {folder_path}/show_mpls_lsp_no-more.txt"}
# #     except Exception as e:
# #         return {"error": f"Error reading file: {str(e)}"}
# # def parse_show_mpls_lsp_p2mp(folder_path: str) -> Dict[str, Any]:
# #     """Parse 'show mpls lsp p2mp | no-more' output"""
# #     try:
# #         cmd = "show mpls lsp p2mp | no-more"
# #         text_content = COMMAND_OUTPUT_STORE.get(cmd)
        
# #         result = ShowMplsLspP2MP()
        
# #         # Parse Ingress LSP section
# #         ingress_header = re.search(r'Ingress LSP:\s+(\d+)\s+sessions', text_content)
# #         if ingress_header:
# #             result.ingress_lsp.total_sessions = int(ingress_header.group(1))
        
# #         # Extract ingress section
# #         if 'Ingress LSP:' in text_content and 'Egress LSP:' in text_content:
# #             ingress_section = text_content.split('Ingress LSP:')[1].split('Egress LSP:')[0]
            
# #             # Parse total line
# #             ingress_total = re.search(r'Total\s+(\d+)\s+displayed,\s+Up\s+(\d+),\s+Down\s+(\d+)', ingress_section)
# #             if ingress_total:
# #                 result.ingress_lsp.sessions_displayed = int(ingress_total.group(1))
# #                 result.ingress_lsp.sessions_up = int(ingress_total.group(2))
# #                 result.ingress_lsp.sessions_down = int(ingress_total.group(3))
            
# #             # Parse P2MP sessions
# #             p2mp_sessions = re.split(r'P2MP name:', ingress_section)[1:]
# #             for session_text in p2mp_sessions:
# #                 lines = session_text.strip().split('\n')
# #                 if not lines:
# #                     continue
                
# #                 # First line: name and branch count
# #                 first_line = lines[0]
# #                 name_match = re.match(r'(.+?),\s+P2MP branch count:\s+(\d+)', first_line)
# #                 if not name_match:
# #                     continue
                
# #                 p2mp_name = name_match.group(1).strip()
# #                 branch_count = int(name_match.group(2))
                
# #                 session = P2MPSession(p2mp_name=p2mp_name, branch_count=branch_count)
                
# #                 # Parse branch entries (skip first line which is header "To From State...")
# #                 branch_pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\w+)\s+(\d+)\s+(\*|\s+)\s+(.+)$'
# #                 for line in lines[1:]:  # Start from line 1 (line 0 is P2MP name line)
# #                     # Skip the header line
# #                     if line.strip().startswith('To'):
# #                         continue
# #                     match = re.match(branch_pattern, line)
# #                     if match:
# #                         branch = P2MPIngressBranch(
# #                             to=match.group(1),
# #                             from_=match.group(2),
# #                             state=match.group(3),
# #                             rt=int(match.group(4)),
# #                             p=match.group(5).strip(),
# #                             active_path='',
# #                             lsp_name=match.group(6).strip()
# #                         )
# #                         session.branches.append(branch)
                
# #                 result.ingress_lsp.sessions.append(session)
        
# #         # Parse Egress LSP section
# #         egress_header = re.search(r'Egress LSP:\s+(\d+)\s+sessions', text_content)
# #         if egress_header:
# #             result.egress_lsp.total_sessions = int(egress_header.group(1))
        
# #         if 'Egress LSP:' in text_content:
# #             egress_section = text_content.split('Egress LSP:')[1]
# #             if 'Transit LSP:' in egress_section:
# #                 egress_section = egress_section.split('Transit LSP:')[0]
            
# #             # Parse total line
# #             egress_total = re.search(r'Total\s+(\d+)\s+displayed,\s+Up\s+(\d+),\s+Down\s+(\d+)', egress_section)
# #             if egress_total:
# #                 result.egress_lsp.sessions_displayed = int(egress_total.group(1))
# #                 result.egress_lsp.sessions_up = int(egress_total.group(2))
# #                 result.egress_lsp.sessions_down = int(egress_total.group(3))
            
# #             # Parse P2MP sessions
# #             p2mp_sessions = re.split(r'P2MP name:', egress_section)[1:]
# #             for session_text in p2mp_sessions:
# #                 lines = session_text.strip().split('\n')
# #                 if not lines:
# #                     continue
                
# #                 # First line: name and branch count
# #                 first_line = lines[0]
# #                 name_match = re.match(r'(.+?),\s+P2MP branch count:\s+(\d+)', first_line)
# #                 if not name_match:
# #                     continue
                
# #                 p2mp_name = name_match.group(1).strip()
# #                 branch_count = int(name_match.group(2))
                
# #                 session = P2MPSession(p2mp_name=p2mp_name, branch_count=branch_count)
                
# #                 # Parse branch entries
# #                 branch_pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+?)$'
# #                 for line in lines[1:]:
# #                     # Skip the header line
# #                     if line.strip().startswith('To'):
# #                         continue
# #                     match = re.match(branch_pattern, line)
# #                     if match:
# #                         branch = P2MPEgressBranch(
# #                             to=match.group(1),
# #                             from_=match.group(2),
# #                             state=match.group(3),
# #                             rt=int(match.group(4)),
# #                             style=f"{match.group(5)} {match.group(6)}",
# #                             label_in=match.group(7),
# #                             label_out=match.group(8),
# #                             lsp_name=match.group(9).strip()
# #                         )
# #                         session.branches.append(branch)
                
# #                 result.egress_lsp.sessions.append(session)
        
# #         # Parse Transit LSP section
# #         transit_header = re.search(r'Transit LSP:\s+(\d+)\s+sessions', text_content)
# #         if transit_header:
# #             result.transit_lsp.total_sessions = int(transit_header.group(1))
        
# #         if 'Transit LSP:' in text_content:
# #             transit_section = text_content.split('Transit LSP:')[1]
            
# #             # Parse P2MP sessions
# #             p2mp_sessions = re.split(r'P2MP name:', transit_section)[1:]
# #             for session_text in p2mp_sessions:
# #                 lines = session_text.strip().split('\n')
# #                 if not lines:
# #                     continue
                
# #                 # First line: name and branch count
# #                 first_line = lines[0]
# #                 name_match = re.match(r'(.+?),\s+P2MP branch count:\s+(\d+)', first_line)
# #                 if not name_match:
# #                     continue
                
# #                 p2mp_name = name_match.group(1).strip()
# #                 branch_count = int(name_match.group(2))
                
# #                 session = P2MPSession(p2mp_name=p2mp_name, branch_count=branch_count)
                
# #                 # Parse branch entries
# #                 branch_pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+?)$'
# #                 for line in lines[1:]:
# #                     # Skip the header line
# #                     if line.strip().startswith('To'):
# #                         continue
# #                     match = re.match(branch_pattern, line)
# #                     if match:
# #                         branch = P2MPTransitBranch(
# #                             to=match.group(1),
# #                             from_=match.group(2),
# #                             state=match.group(3),
# #                             rt=int(match.group(4)),
# #                             style=f"{match.group(5)} {match.group(6)}",
# #                             label_in=match.group(7),
# #                             label_out=match.group(8),
# #                             lsp_name=match.group(9).strip()
# #                         )
# #                         session.branches.append(branch)
                
# #                 result.transit_lsp.sessions.append(session)
            
# #             # Count displayed, up, down from entries
# #             total_branches = sum(len(s.branches) for s in result.transit_lsp.sessions)
# #             result.transit_lsp.sessions_displayed = total_branches
# #             result.transit_lsp.sessions_up = sum(1 for s in result.transit_lsp.sessions for b in s.branches if b.state == 'Up')
# #             result.transit_lsp.sessions_down = sum(1 for s in result.transit_lsp.sessions for b in s.branches if b.state == 'Down')
        
# #         result_dict = asdict(result)
# #         return result_dict
        
# #     except FileNotFoundError:
# #         return {"error": f"File not found: {folder_path}/show_mpls_lsp_p2mp_no-more.txt"}
# #     except Exception as e:
# #         return {"error": f"Error reading file: {str(e)}"}
# # def parse_show_bgp_summary(folder_path: str) -> Dict[str, Any]:
# #     """Parse 'show bgp summary | no-more' output"""
# #     try:
# #         cmd = "show bgp summary | no-more"
# #         text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #         print(text_content)
        
# #         # Create a dictionary with the text content under the key "output"
# #         result = {
# #             "output": text_content
# #         }
        
# #         return result
        
# #     except FileNotFoundError:
# #         return {"error": f"File not found: {folder_path}/show_bgp_summary_no-more.txt"}
# #     except Exception as e:
# #         return {"error": f"Error reading file: {str(e)}"}
# # def parse_show_bgp_neighbor(folder_path: str) -> Dict[str, Any]:
# #     """Parse 'show bgp neighbor | no-more' output"""
# #     try:
# #         cmd = "show bgp neighbor | no-more"
# #         text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #         print(text_content)
        
# #         # Create a dictionary with the text content under the key "output"
# #         result = {
# #             "output": text_content
# #         }
        
# #         return result
        
# #     except FileNotFoundError:
# #         return {"error": f"File not found: {folder_path}/show_bgp_neighbor_no-more.txt"}
# #     except Exception as e:
# #         return {"error": f"Error reading file: {str(e)}"}
# # def parse_show_isis_adjacency_extensive(folder_path: str) -> dict[str, any]:
# #     """Parse 'show isis adjacency extensive | no-more' output"""
# #     cmd = "show isis adjacency extensive | no-more"
# #     text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #     print(text_content,"\n","\n")
# #     result = ShowIsisAdjacencyExtensive()
    
# #     adjacency_sections = re.split(r'\n(?=[A-Z0-9]+\n\s+Interface:)', text_content)
    
# #     for section in adjacency_sections:
# #         if not section.strip():
# #             continue
        
# #         system_match = re.match(r'^([A-Z0-9]+)', section)
# #         if not system_match:
# #             continue
        
# #         entry = ShowIsisAdjacencyEntry(
# #             system_name=system_match.group(1),
# #             interface="",
# #             level="",
# #             state="",
# #             expires_in="",
# #             priority="",
# #             up_down_transitions=0,
# #             last_transition="",
# #             circuit_type="",
# #             speaks="",
# #             topologies="",
# #             restart_capable="",
# #             adjacency_advertisement=""
# #         )
        
# #         # Fixed: Remove trailing comma from interface
# #         interface_match = re.search(r'Interface:\s+(\S+),', section)
# #         if interface_match:
# #             entry.interface = interface_match.group(1)
        
# #         level_match = re.search(r'Level:\s+(\d+)', section)
# #         if level_match:
# #             entry.level = level_match.group(1)
        
# #         state_match = re.search(r'State:\s+(\w+)', section)
# #         if state_match:
# #             entry.state = state_match.group(1)
        
# #         expires_match = re.search(r'Expires in\s+(\d+\s+secs)', section)
# #         if expires_match:
# #             entry.expires_in = expires_match.group(1)
        
# #         priority_match = re.search(r'Priority:\s+(\d+)', section)
# #         if priority_match:
# #             entry.priority = priority_match.group(1)
        
# #         transitions_match = re.search(r'Up/Down transitions:\s+(\d+)', section)
# #         if transitions_match:
# #             entry.up_down_transitions = int(transitions_match.group(1))
        
# #         last_trans_match = re.search(r'Last transition:\s+(.+?)(?:\n|$)', section)
# #         if last_trans_match:
# #             entry.last_transition = last_trans_match.group(1)
        
# #         circuit_type_match = re.search(r'Circuit type:\s+(\d+)', section)
# #         if circuit_type_match:
# #             entry.circuit_type = circuit_type_match.group(1)
        
# #         # Fixed: Capture both IP and IPv6
# #         speaks_match = re.search(r'Speaks:\s+(.+?)(?:\n)', section)
# #         if speaks_match:
# #             entry.speaks = speaks_match.group(1).strip()
        
# #         topologies_match = re.search(r'Topologies:\s+(.+)', section)
# #         if topologies_match:
# #             entry.topologies = topologies_match.group(1).strip()
        
# #         restart_match = re.search(r'Restart capable:\s+(\w+)', section)
# #         if restart_match:
# #             entry.restart_capable = restart_match.group(1)
        
# #         adj_adv_match = re.search(r'Adjacency advertisement:\s+(.+)', section)
# #         if adj_adv_match:
# #             entry.adjacency_advertisement = adj_adv_match.group(1).strip()
        
# #         ip_match = re.search(r'IP addresses:\s+(.+)', section)
# #         if ip_match:
# #             entry.ip_addresses = [ip_match.group(1).strip()]
        
# #         # Parse Adj-SID entries
# #         adj_sid_pattern = r'Level\s+(\d+)\s+(IPv[46])\s+(\w+)\s+Adj-SID:\s+(\d+),\s+Flags:\s+(.+)'
# #         for adj_match in re.finditer(adj_sid_pattern, section):
# #             adj_sid = {
# #                 'level': adj_match.group(1),
# #                 'ip_version': adj_match.group(2),
# #                 'protection': adj_match.group(3),
# #                 'sid': adj_match.group(4),
# #                 'flags': adj_match.group(5).strip()
# #             }
# #             entry.adj_sids.append(adj_sid)
        
# #         # FIXED: Parse Transition log using column positions
# #         transition_log_match = re.search(
# #             r'Transition log:\s*\n\s+(When\s+State\s+Event\s+Down reason)\s*\n((?:\s+\S.*\n?)+)', 
# #             section
# #         )
# #         if transition_log_match:
# #             header_line = transition_log_match.group(1)
# #             log_text = transition_log_match.group(2)
            
# #             for line in log_text.strip().split('\n'):
# #                 if not line.strip():
# #                     continue
                
# #                 # Use regex to parse fixed-width columns
# #                 # Format: "  Thu Feb  6 12:35:10   Up           Seenself"
# #                 # or:     "  Tue May  6 02:40:15   Down         Interface Down  Interface Down"
                
# #                 # Match timestamp (format: DDD MMM DD HH:MM:SS or DDD MMM  D HH:MM:SS)
# #                 # Note: Day can be single digit with extra space (e.g., "Feb  6")
# #                 match = re.match(
# #                     r'\s+(\w{3}\s+\w{3}\s+\d{1,2}\s+\d+:\d+:\d+)\s+(\w+)\s+(.+)',
# #                     line
# #                 )
                
# #                 if match:
# #                     timestamp = match.group(1)
# #                     state = match.group(2)
# #                     rest = match.group(3).strip()
                    
# #                     # Now split the rest into Event and Down reason
# #                     # The Event and Down reason are separated by multiple spaces (at least 2)
# #                     # Split on 2+ consecutive spaces
# #                     parts = re.split(r'\s{2,}', rest, maxsplit=1)
                    
# #                     event = parts[0].strip()
# #                     down_reason = parts[1].strip() if len(parts) > 1 else ''
                    
# #                     transition = ShowIsisAdjacencyTransition(
# #                         when=timestamp,
# #                         state=state,
# #                         event=event,
# #                         down_reason=down_reason
# #                     )
# #                     entry.transition_log.append(transition)
        
# #         result.entries.append(entry)
    
# #     r = asdict(result)
# #     print(r)
# #     return r
# # def parse_show_route_summary(folder_path: str) -> dict[str, any]:
# #     """Parse 'show route summary | no-more' output"""
# #     cmd = "show route summary | no-more"
# #     text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #     print(text_content,"\n","\n")
    
# #     result = ShowRouteSummary()
    
# #     as_match = re.search(r'Autonomous system number:\s+(\d+)', text_content)
# #     if as_match:
# #         result.autonomous_system = as_match.group(1)
    
# #     router_id_match = re.search(r'Router ID:\s+(\S+)', text_content)
# #     if router_id_match:
# #         result.router_id = router_id_match.group(1)
    
# #     highwater = ShowRouteSummaryHighwater()
# #     hw_match = re.search(r'RIB unique destination routes:\s+(.+)', text_content)
# #     if hw_match:
# #         highwater.rib_unique_destination_routes = hw_match.group(1).strip()
    
# #     hw_routes_match = re.search(r'RIB routes\s+:\s+(.+)', text_content)
# #     if hw_routes_match:
# #         highwater.rib_routes = hw_routes_match.group(1).strip()
    
# #     hw_fib_match = re.search(r'FIB routes\s+:\s+(.+)', text_content)
# #     if hw_fib_match:
# #         highwater.fib_routes = hw_fib_match.group(1).strip()
    
# #     hw_vrf_match = re.search(r'VRF type routing instances\s+:\s+(.+)', text_content)
# #     if hw_vrf_match:
# #         highwater.vrf_type_routing_instances = hw_vrf_match.group(1).strip()
    
# #     result.highwater = highwater
    
# #     # Pattern to match table headers
# #     table_pattern = r'^(\S+(?:\.\S+)?): (\d+) destinations, (\d+) routes \((\d+) active, (\d+) holddown, (\d+) hidden\)'
# #     # Pattern to match protocol lines - FIXED: removed '?' after 'routes' to make it required
# #     protocol_pattern = r'^\s+(\S+):\s+(\d+) routes,\s+(\d+) active'
    
# #     tables_section = text_content.split('Highwater Mark')[1] if 'Highwater Mark' in text_content else text_content
    
# #     current_table = None
# #     for line in tables_section.split('\n'):
# #         table_match = re.match(table_pattern, line.strip())
# #         if table_match:
# #             current_table = ShowRouteSummaryTable(
# #                 table_name=table_match.group(1),
# #                 destinations=int(table_match.group(2)),
# #                 routes=int(table_match.group(3)),
# #                 active=int(table_match.group(4)),
# #                 holddown=int(table_match.group(5)),
# #                 hidden=int(table_match.group(6))
# #             )
# #             result.tables.append(current_table)
# #         elif current_table:
# #             # Check protocol line - don't strip() before matching to preserve leading whitespace
# #             protocol_match = re.match(protocol_pattern, line)
# #             if protocol_match:
# #                 protocol = ShowRouteSummaryProtocol(
# #                     protocol=protocol_match.group(1),
# #                     routes=int(protocol_match.group(2)),
# #                     active=int(protocol_match.group(3))
# #                 )
# #                 current_table.protocols.append(protocol)
    
# #     r = asdict(result)
# #     print(r)
# #     return r
# # def parse_show_rsvp_session_match_DN(folder_path: str) -> Dict[str, Any]:
# #     """Parse 'show rsvp session match DN | no-more' output"""
# #     print('parse_show_mpls_lsp_unidirectional_match_DN')
# #     try:
# #         cmd = "show rsvp session match DN | no-more"
# #         text_content = COMMAND_OUTPUT_STORE.get(cmd).strip()
        
# #         print(text_content)
# #         # Check if file is empty or contains "empty" string
        
# #         if not text_content or "empty" in text_content.lower():
# #             return {}
        
# #         # Create a dictionary with the text content under the key "output"
# #         result = {
# #             "output": text_content
# #         }
# #         print(result)
# #         return result
        
# #     except FileNotFoundError:
# #         return {"error": f"File not found: {file_path}"}
# #     except Exception as e:
# #         return {"error": f"Error reading file: {str(e)}"}
# # def parse_show_mpls_lsp_unidirectional_match_DN(folder_path: str) -> Dict[str, Any]:
# #     """Parse 'show mpls lsp unidirectional match DN | no-more' output"""
# #     cmd = "show mpls lsp unidirectional match DN | no-more"
# #     text_content = COMMAND_OUTPUT_STORE.get(cmd)
    
# #     if text_content:
# #         text_content = text_content.strip()
    
# #     # print("from COMMAND_OUTPUT_STORE - ", text_content)
# #     print("===")
# #     print(text_content)
# #     if not text_content or "empty" in text_content.lower():
# #         return {}
    
# #     result = {"output": text_content}
# #     print(result)
# #     return result
# # def parse_show_rsvp(folder_path: str) -> Dict[str, Any]:
# #     """Parse show rsvp output"""
# #     try:
# #         cmd = "show rsvp"
# #         text_content = COMMAND_OUTPUT_STORE.get(cmd)
# #         print(text_content)
# #         #print(result_dict)
        
# #         # Remove pagination markers
# #         text_content = re.sub(r'---(more)---\s*\n?', '', text_content)
        
# #         result = ShowRsvpData()
        
# #         # Split by sections (Ingress, Egress, Transit)
# #         sections = re.split(r'((?:Ingress|Egress|Transit) RSVP: \d+ sessions)', text_content)
        
# #         for i in range(1, len(sections), 2):
# #             section_header = sections[i].strip()
# #             section_content = sections[i + 1] if i + 1 < len(sections) else ""
            
# #             # Determine section type and extract total sessions from header
# #             section_type = None
# #             total_sessions = 0
            
# #             if "Ingress" in section_header:
# #                 section_type = "Ingress"
# #                 total_match = re.search(r'Ingress RSVP: (\d+) sessions', section_header)
# #                 total_sessions = int(total_match.group(1)) if total_match else 0
# #             elif "Egress" in section_header:
# #                 section_type = "Egress"
# #                 total_match = re.search(r'Egress RSVP: (\d+) sessions', section_header)
# #                 total_sessions = int(total_match.group(1)) if total_match else 0
# #             elif "Transit" in section_header:
# #                 section_type = "Transit"
# #                 total_match = re.search(r'Transit RSVP: (\d+) sessions', section_header)
# #                 total_sessions = int(total_match.group(1)) if total_match else 0
# #             else:
# #                 continue
            
# #             # Extract summary line (Total X displayed, Up Y, Down Z)
# #             summary_match = re.search(r'Total\s+(\d+)\s+displayed,\s+Up\s+(\d+),\s+Down\s+(\d+)', section_content)
# #             sessions_up = int(summary_match.group(2)) if summary_match else 0
# #             sessions_down = int(summary_match.group(3)) if summary_match else 0
            
# #             # Parse entries - pattern for data rows
# #             # Format: To From State Rt Style Labelin Labelout LSPname
# #             pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(Up|Down)\s+(\d+)\s+(\d+)\s+(\w+)\s+(\S+)\s+(\S+)\s+(\S+)$'
            
# #             entries = []
# #             for match in re.finditer(pattern, section_content, re.MULTILINE):
# #                 entry = RsvpSessionEntry(
# #                     to_address=match.group(1),
# #                     from_address=match.group(2),
# #                     state=match.group(3),
# #                     rt=int(match.group(4)),
# #                     style=f"{match.group(5)} {match.group(6)}",
# #                     label_in=match.group(7),
# #                     label_out=match.group(8),
# #                     lsp_name=match.group(9).strip()
# #                 )
# #                 entries.append(entry)
            
# #             # Create section object
# #             rsvp_section = RsvpSection(
# #                 section_type=section_type,
# #                 total_sessions=total_sessions,
# #                 sessions_up=sessions_up,
# #                 sessions_down=sessions_down,
# #                 entries=entries
# #             )
            
# #             # If "Total" line wasn't found, calculate from entries
# #             if rsvp_section.sessions_up == 0 and rsvp_section.sessions_down == 0 and entries:
# #                 for entry in entries:
# #                     if entry.state == 'Up':
# #                         rsvp_section.sessions_up += 1
# #                     else:
# #                         rsvp_section.sessions_down += 1
            
# #             # Assign to appropriate section
# #             if section_type == "Ingress":
# #                 result.ingress = rsvp_section
# #             elif section_type == "Egress":
# #                 result.egress = rsvp_section
# #             elif section_type == "Transit":
# #                 result.transit = rsvp_section
        
# #         result_dict = asdict(result)
# #         #print(result_dict)
# #         return result_dict
        
# #     except FileNotFoundError:
# #         return {"error": f"File not found: {folder_path}/show_rsvp.txt"}
# #     except Exception as e:
# #         return {"error": f"Error reading file: {str(e)}"}
# # def parse_show_mpls_lsp_unidirectional_no_more(folder_path: str) -> Dict[str, Any]:
# #     """Parse show mpls lsp unidirectional no more output"""
# #     try:
# #         cmd = "show mpls lsp unidirectional no more"
# #         text_content = COMMAND_OUTPUT_STORE.get(cmd)
        
# #         print(result_dict)
# #         # Remove pagination markers
# #         text_content = re.sub(r'---(more)---\s*\n?', '', text_content)
        
# #         result = ShowMplsLspData()
        
# #         # Split by sections (Ingress, Egress, Transit)
# #         sections = re.split(r'((?:Ingress|Egress|Transit) LSP: \d+ sessions)', text_content)
        
# #         for i in range(1, len(sections), 2):
# #             section_header = sections[i].strip()
# #             section_content = sections[i + 1] if i + 1 < len(sections) else ""
            
# #             # Determine section type and extract total sessions from header
# #             section_type = None
# #             total_sessions = 0
            
# #             if "Ingress" in section_header:
# #                 section_type = "Ingress"
# #                 total_match = re.search(r'Ingress LSP: (\d+) sessions', section_header)
# #                 total_sessions = int(total_match.group(1)) if total_match else 0
# #             elif "Egress" in section_header:
# #                 section_type = "Egress"
# #                 total_match = re.search(r'Egress LSP: (\d+) sessions', section_header)
# #                 total_sessions = int(total_match.group(1)) if total_match else 0
# #             elif "Transit" in section_header:
# #                 section_type = "Transit"
# #                 total_match = re.search(r'Transit LSP: (\d+) sessions', section_header)
# #                 total_sessions = int(total_match.group(1)) if total_match else 0
# #             else:
# #                 continue
            
# #             # Extract summary line (Total X displayed, Up Y, Down Z)
# #             summary_match = re.search(r'Total\s+(\d+)\s+displayed,\s+Up\s+(\d+),\s+Down\s+(\d+)', section_content)
# #             sessions_displayed = int(summary_match.group(1)) if summary_match else 0
# #             sessions_up = int(summary_match.group(2)) if summary_match else 0
# #             sessions_down = int(summary_match.group(3)) if summary_match else 0
            
# #             # Parse entries - pattern for data rows
# #             # Format: To From State Rt Style Labelin Labelout LSPname
# #             pattern = r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(Up|Down)\s+(\d+)\s+(\d+)\s+(\w+)\s+(\S+)\s+(\S+)\s+(\S+)$'
            
# #             entries = []
# #             for match in re.finditer(pattern, section_content, re.MULTILINE):
# #                 entry = MplsLspEntry(
# #                     to_address=match.group(1),
# #                     from_address=match.group(2),
# #                     state=match.group(3),
# #                     rt=int(match.group(4)),
# #                     style=f"{match.group(5)} {match.group(6)}",
# #                     label_in=match.group(7),
# #                     label_out=match.group(8),
# #                     lsp_name=match.group(9).strip()
# #                 )
# #                 entries.append(entry)
            
# #             # Create section object
# #             mpls_lsp_section = MplsLspSection(
# #                 section_type=section_type,
# #                 total_sessions=total_sessions,
# #                 sessions_displayed=sessions_displayed,
# #                 sessions_up=sessions_up,
# #                 sessions_down=sessions_down,
# #                 entries=entries
# #             )
            
# #             # Assign to appropriate section
# #             if section_type == "Ingress":
# #                 result.ingress = mpls_lsp_section
# #             elif section_type == "Egress":
# #                 result.egress = mpls_lsp_section
# #             elif section_type == "Transit":
# #                 result.transit = mpls_lsp_section
        
# #         # Calculate from entries if "Total" line wasn't found
# #         if result.ingress and result.ingress.sessions_displayed == 0 and result.ingress.entries:
# #             for entry in result.ingress.entries:
# #                 result.ingress.sessions_displayed += 1
# #                 if entry.state == 'Up':
# #                     result.ingress.sessions_up += 1
# #                 else:
# #                     result.ingress.sessions_down += 1
        
# #         if result.egress and result.egress.sessions_displayed == 0 and result.egress.entries:
# #             for entry in result.egress.entries:
# #                 result.egress.sessions_displayed += 1
# #                 if entry.state == 'Up':
# #                     result.egress.sessions_up += 1
# #                 else:
# #                     result.egress.sessions_down += 1
        
# #         if result.transit and result.transit.sessions_displayed == 0 and result.transit.entries:
# #             for entry in result.transit.entries:
# #                 result.transit.sessions_displayed += 1
# #                 if entry.state == 'Up':
# #                     result.transit.sessions_up += 1
# #                 else:
# #                     result.transit.sessions_down += 1
        
# #         result_dict = asdict(result)
# #         #print(result_dict)
# #         return result_dict
        
# #     except FileNotFoundError:
# #         return {"error": f"File not found: {folder_path}/show_mpls_lsp_unidirectional_no-more.txt"}
# #     except Exception as e:
# #         return {"error": f"Error reading file: {str(e)}"}



# # if __name__ == '__main__':
# #     if len(sys.argv) != 2:
# #         print("Usage: python mx_parser.py <folder_path>")
# #         sys.exit(1)

# #     folder_path = sys.argv[1]
# #     results = {}

# #     results["1_show_arp_no_resolve"] = parse_show_arp_no_resolve(folder_path)
# #     results["2_show_vrrp_summary"] = parse_show_vrrp_summary(folder_path)
# #     results["3_show_lldp_neighbors"] = parse_show_lldp_neighbors(folder_path)
# #     results["4_show_bfd_session"] = parse_show_bfd_session(folder_path)
# #     results["5_show_rsvp_neighbor"] = parse_show_rsvp_neighbor(folder_path)
# #     results["6_show_rsvp_session"] = parse_show_rsvp_session(folder_path)
# #     results["7_show_route_table_inet0"] = parse_show_route_table_inet0(folder_path)
# #     results["8_show_route_table_inet3"] = parse_show_route_table_inet3(folder_path)
# #     results["9_show_route_table_mpls0"] = parse_show_route_table_mpls0(folder_path)
# #     results["10_show_mpls_interface"] = parse_show_mpls_interface(folder_path)
# #     results["11_show_mpls_lsp"] = parse_show_mpls_lsp(folder_path)
# #     results["12_show_mpls_lsp_p2mp"] = parse_show_mpls_lsp_p2mp(folder_path)
# #     results["13_show_bgp_summary"] = parse_show_bgp_summary(folder_path)
# #     results["14_show_bgp_neighbor"] = parse_show_bgp_neighbor(folder_path)
# #     results["15_show_isis_adjacency_extensive"] = parse_show_isis_adjacency_extensive(folder_path)
# #     results["16_show_route_summary"] = parse_show_route_summary(folder_path)
# #     results["17_show_rsvp_session_match_DN"] = parse_show_rsvp_session_match_DN(folder_path)
# #     results["18_show_mpls_lsp_unidirectional_match_DN"] = parse_show_mpls_lsp_unidirectional_match_DN(folder_path)
# #     results["19_show_rsvp"] = parse_show_rsvp(folder_path)
# #     results["20_show_mpls_lsp_unidirectional_no_more"] = parse_show_mpls_lsp_unidirectional_no_more(folder_path)

# #     print(results)

































