import re
import json
from dataclasses import asdict
from models.cisco.cisco_ncs5501 import *
from typing import Any, Dict




def show_inventory(text_content): 
    """
    Function: show_inventory
    Purpose: Display the product inventory of all Cisco products
            installed in the networking device. 
    command: show inventory
    """
    cmd = "show inventory"
    try:

        result = {}
        pattern = re.compile(
            r'NAME:\s*"(?P<NAME>[^"]+)",\s*DESCR:\s*"(?P<DESCR>[^"]+)"\s*'
            r'[\s\n]'
            r'PID:\s*(?P<PID>[^,]+?)\s*,\s*'
            r'VID:\s*(?P<VID>[^,]+?)\s*,\s*'
            r'SN:\s*(?P<SN>\S+)'
        )  

        inventory = []

        matches = list(pattern.finditer(text_content))

        for match in matches: 
            inventory.append(
                asdict(
                    ShowInventory(
                        NAME=match.group("NAME").strip(), 
                        DESCR=match.group("DESCR").strip(), 
                        PID=match.group("PID").strip(), 
                        VID=match.group("VID").strip(), 
                        SN=match.group("SN").strip(),
                    )
                )
            )
        total_count = len(inventory)
        result = {
            "totalCount": total_count, 
            "inventory": inventory
        }
        
        if not result: 
            return {"info": "No inventory found"}

        return result

    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}

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
            r'^\s+(?!Active)(?!Label)(?!Mon|Tue|Wed|Thur|Fri|Sat|Sun)(\S+)',
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
    
def show_install_committed_summary(text_content): 
    """
    Docstring for show_install_committed_summary
    
    :param folder_path: Description
    :type folder_path: str
    :return: Description
    :rtype: Dict[str, Any]
    """
    cmd = "show install committed summary"
    try: 

        result = {}        
        match = re.search(
            r'Committed Packages:\s*(?P<count>\d+)',
            text_content
        )

        committedPackages = int(match.group("count")) if match else 0 

        label_match = re.search(
            r'^\s*Label\s*:\s*(?P<labels>.+?)\s*$', 
            text_content, 
            re.MULTILINE
        )
        labels = label_match.group("labels") if label_match else "unknown"

        package = re.findall(
            r'^\s+(?!Committed)(?!Label)(?!Mon|Tue|Wed|Thur|Fri|Sat|Sun)(\S+)', 
            text_content, 
            re.MULTILINE
        )

        packages = [line.strip() for line in package  if line.strip() ]

        result = asdict(
            ShowInstallCommittedSummary(
                Label = labels, 
                CommittedPackages= committedPackages, 
                Packages=packages
            )
        )

        if not result: 
            return {"info": "No Committed summary found"}
          
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

def show_route_summary(text_content): 
    """
    Docstring for show_route_summary
    
    :param folder_path: Description
    :type folder_path: str
    """
    cmd = "show route summary"
    try: 
        result = {}
        
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
            return {"info": "No watchdoc memroy state found"}

        return result
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_ipv4_vrf_all_interface_brief(text_content):
    cmd = "show ipv4 vrf all interface brief"
    try:
        result = {}

        int_brief = []

        ip_regex = r'\d+\.\d+\.\d+\.\d+'
        
        pattern = re.compile(
            rf'^(?P<Interface>\S+)\s+'
            rf'(?P<IPAddress>{ip_regex}|unassigned)?\s*'
            rf'(?P<Status>Up|Down|Shutdown)\s+'
            rf'(?P<Protocol>Up|Down)\s+'
            rf'(?P<VrfName>\S+)',
            re.MULTILINE
        )

        for m in pattern.finditer(text_content):
            try:
                row = m.groupdict()
                if not row["IPAddress"]: 
                    row["IPAddress"] = "unassigned"

                entry = ShowIpv4VrfAllInterfaceBrief(
                    interface=m.group("Interface"),
                    IPAddress=m.group("IPAddress"),
                    status=m.group("Status"),
                    protocol=m.group("Protocol"),
                    VRFName=m.group("VrfName")
                )
                int_brief.append(asdict(entry))
            except Exception as row_error:
                return {"error": f"Error parsing {cmd}: {str(row_error)}"}
        total_count = len(int_brief)

        result = {
            "totalCount": total_count, 
            "VRFInterfaces": int_brief
        }

        if not result: 
            return {"info": "No vrf interface details found"}

        return result
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_lldp_neighbors(text_content):
    cmd = "show lldp neighbors"
    try:
        result = {}
        neighbors = []

        match = re.search(
            r'Total\sentries\sdisplayed:\s*(?P<count>\d+)$',
            text_content
        )
        total_neighbors = int(match.group("count")) if match else 0  # need to fix, taking 0 only as value

        for line in text_content.splitlines():
            line = line.strip()
            
            if(
                not line
                or line.startswith("Capability")
                or line.startswith("(")
                or line.startswith("Device ID")
                or line.startswith("Total")
            ):
                continue

            cols = re.split(r'\s{1,}', line)

            entry = lldpNeighbors(
                deviceId = cols[0],
                localIntf = cols[1],
                holdTime = cols[2],
                capability = cols[3],
                portId = cols[4]
            )
            neighbors.append(asdict(entry))

        result = {
            "Total entries displayed": total_neighbors,
            "neighbors": neighbors
        }

        if not result: 
            return {"info": "No LLDP neighbors found"}
          
        return result
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_isis_adjacency(content: str) -> List[Dict[str, Any]]:
    """
    Parse 'show isis adjacency' output.

    :param content: Raw command output string.
    :return: List of parsed dicts.
    """
    try:
        cmd = "show isis adjacency"
        
        if not content:
            raise ValueError(f"No output found for command: {cmd}")

        result, adjacencies = {}, []

        match = re.search(
            r'^IS-IS\s\S+\sLevel-(?P<adjacencyLevel>\d+)',
            content,
            re.MULTILINE
        )
        adjacencyLevel = int(match.group("adjacencyLevel")) if match else 0

        for line in content.splitlines():
            line = line.strip()

            if (
                not line
                or line.startswith("System")
                or line.startswith("IS-IS")
                or line.startswith("Total")
                or line.startswith("BFD")
            ):
                continue

            cols = re.split(r'\s{1,}', line)
            if len(cols) < 9:
                continue

            entry = ISISAdjacencies(
                systemID=cols[0],
                interface=cols[1],
                SNPA=cols[2],
                state=cols[3],
                hold=cols[4],
                changed=cols[5],
                NSF=cols[6],
                ipv4BFD=cols[7],
                ipv6BFD=cols[8]
            )
            adjacencies.append(asdict(entry))

        total_match = re.search(
            r'^Total\s+adjacency\s+count:\s*(?P<adjacencyCount>\d+)',
            content,
            re.MULTILINE
        )
        adjacencyCount = int(total_match.group("adjacencyCount")) if total_match else 0
        
        if not  adjacencies:
          return {"info":"No ISIS adjacencies found"}
        result = {
            "ISISColtAdjacencyLevel": adjacencyLevel,
            "adjacencies": adjacencies,
            "totalAdjacency": adjacencyCount
        }

        return result

    except Exception as e:
        return [{"error": f"Error parsing command output: {str(e)}"}]

                                             
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

def show_mpls_forwarding_summary(text_content): 
    """
    Docstring for show_mpls_forwarding_summary
    
    :param folder_path: Description
    :type folder_path: str
    :return: Description
    :rtype: Dict[str, Any]
    """
    cmd = "show mpls forwarding summary"
    try: 

        mpls_output = {}
        # Regex patterns
        label_switching_pattern = re.compile(
            r"Label switching:\s*(?P<labelSwitching>\d+),\s*protected:\s*(?P<labelSwitchingProtected>\d+)\s*\(Ready:\s*(?P<labelSwitchingReady>\d+),\s*Active:\s*(?P<labelSwitchingActive>\d+)\)"
        )

        mpls_te_tunnel_pattern = re.compile(
            r"MPLS TE tunnel head:\s*(?P<mplsTETunnellHead>\d+),\s*protected:\s*(?P<mplsTETunnellHeadProtected>\d+)"
        )

        forwarding_msg_updates = re.compile(
            r"messages:\s*(?P<messages>\d+)\s*.*p2p updates:\s*(?P<p2pUpdates>\d+)"
        )
        pkts_dropped_pattern = re.compile(
            r"Pkts dropped:\s*(?P<pktsDropped>\d+)"
        )

        pkts_fragments_pattern = re.compile(
            r"Pkts fragmented:\s*(?P<pktsFragmented>\d+)"
        )

        failed_lookup_pattern = re.compile(
            r"Failed lookups:\s*(?P<failedLookups>\d+)"
        )

        labels_in_use_pattern = re.compile(
            r"Reserved:\s*(?P<reserved>\d+).*Lowest:\s*(?P<lowest>\d+).*Highest:\s*(?P<highest>\d+).*Deleted stale label entries:\s*(?P<deletedStaleLabelEntries>\d+)",
            re.DOTALL
        )

        # Safe matching
        ls_match = label_switching_pattern.search(text_content)
        te_match = mpls_te_tunnel_pattern.search(text_content)
        fu_match = forwarding_msg_updates.search(text_content)
        lu_match = labels_in_use_pattern.search(text_content)
        pkts_droped = pkts_dropped_pattern.search(text_content).group("pktsDropped")
        pkts_fragmented = pkts_fragments_pattern.search(text_content).group("pktsFragmented")
        failed_lookups = failed_lookup_pattern.search(text_content).group("failedLookups")

        if not (ls_match and te_match and fu_match and lu_match ):
            raise ValueError("Regex did not match expected output format")

        # Build dataclasses using groupdict
        fe = ForwardingEntries(**{k: int(v) for k, v in {**ls_match.groupdict(), **te_match.groupdict()}.items()})
        fu = ForwardingUpdates(**{k: int(v) for k, v in fu_match.groupdict().items()})
        lu = LabelsInUse(**{k: int(v) for k, v in lu_match.groupdict().items()})


        mpls_output = {
            "ForwardingEntries": asdict(fe),
            "ForwardingUpdates": asdict(fu),
            "LabelsInUse": asdict(lu),
            "PktsDropped": pkts_droped, 
            "PktsFragmented": pkts_fragmented, 
            "FailedLookUps": failed_lookups
        }

        if not mpls_output: 
            return {"info": "MPLS forwarding Summary not found"}

        return mpls_output
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"} 

def show_l2vpn_xconnect_summary(text_content): 
    """
    Docstring for show_l2vpn_xconnect_summary
    
    :param folder_path: Description
    :type folder_path: str
    :return: Description
    :rtype: Dict[str, Any]
    """
    cmd = "show l2vpn xconnect summary"
    try: 
        
        result = {}

        group_pattern = re.compile(
            r"Number of groups:\s*(?P<groups>\d+)\s*Number of xconnects:\s*(?P<xconnects>\d+)"
        )

        xconnects_status_pattern = re.compile(
            r"Up:\s*(?P<up>\d+)\s*Down:\s*(?P<down>\d+)"
        )
        
        admin_down_pattern = re.compile(
            r"Number of Admin Down segments:\s*(?P<adminDownSegments>\d+)"
        )

        mp2mp_pattern = re.compile(
            r"Number of MP2MP xconnects:\s*(?P<m2mpXconnects>\d+)\s*\n\s*"
            r"Up\s*(?P<m2mpUp>\d+)\s*Down\s*(?P<m2mpDown>\d+)"
        )

        ce_connection = re.compile(
            r"Number of CE Connections:\s*(?P<ceConnections>\d+).\s*Advertised:\s*(?P<ceAdvertised>\d+)\s*Non-Advertised:\s*(?P<ceNonAdvertised>\d+)", 
            re.DOTALL
        )

        groups = group_pattern.search(text_content)
        xstatus = xconnects_status_pattern.search(text_content)
        admin = admin_down_pattern.search(text_content)
        m2mp = mp2mp_pattern.search(text_content)
        ce = ce_connection.search(text_content)
        
        xinfo = XconnectInfo(
            numberofXconnect = int(groups.group("xconnects")), 
            up = int(xstatus.group("up")), 
            down = int(xstatus.group("down"))
        )
        m2mpInfo = m2mpXconnectsInfo(
            m2mpXconnections=int(m2mp.group('m2mpXconnects')), 
            up = int(m2mp.group('m2mpUp')), 
            down = int(m2mp.group('m2mpDown'))
        )
        m2mp = asdict(m2mpInfo)
        xconnect = asdict(xinfo)

        summary = Showl2vpnXconnectSummary(
            numberOfGroups=int(groups.group("groups")), 
            xconnect=xconnect, 
            adminDownSegments=int(admin.group("adminDownSegments")), 
            m2mpXconnects=m2mp, 
            ceConnections = {
                "ceConnections": int(ce.group("ceConnections")), 
                "advertised": int(ce.group("ceAdvertised")), 
                "nonAdvertised": int(ce.group("ceNonAdvertised"))
            }
        )
        result = asdict(summary)

        if not result: 
            return {"info": "L2VPN summary not found"}

        return result
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"} 
        
def ncs_show_version(text_content): 
    """
    Docstring for show_version
    
    :param folder_path: Description
    :type folder_path: str
    :return: Description
    :rtype: Dict[str, Any]
    """
    cmd = "show version"
    try: 
        
        result = {}

        version_pattern = re.compile(
            r"Version\s*(?P<version>\d+\.\d+\.\d+)"
        )
        system_uptime_pattern = re.compile(
            r"System uptime is\s*(?P<uptime>(?:\d+\s+(?:weeks|days|hours|minutes)\s*)+)"
        )

        model_pattern = re.compile(
            r"cisco\s*(?P<model>(\b([A-Z0-9]+-[A-Z0-9]+)\b))"
        )

        version = version_pattern.search(text_content).group("version")
        model = model_pattern.search(text_content).group("model").lower()
        uptime = system_uptime_pattern.search(text_content).group("uptime").strip()

        entry = ShowVersion(
            version=version, 
            model = model,
            systemUptime = uptime
        )

        result = asdict(entry)

        if not result: 
            return {"info": "No able to get the device version"}

        return result

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"} 

def show_proc_cpu(text_content): 
    """
    Docstring for show_proc_cpu
    
    :param folder_path: Description
    :type folder_path: str
    :return: Description
    :rtype: Dict[str, Any]
    """
    cmd = "show proc cpu"
    try: 
        
        result = {}

        utilization_pattern = re.compile(
            r"CPU utilization for one minute:\s*(?P<one_min>\d+%)\s*;\s*five minutes:\s*(?P<five_min>\d+%)\s*;\s*fifteen minutes:\s*(?P<fifteen_min>\d+%)"
        )

        utilization = utilization_pattern.search(text_content)
        
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

def show_bfd_session(text_content): 
    """
    Docstring for show_bfd_session
    
    :param folder_path: Description
    :type folder_path: str
    :return: Description
    :rtype: Dict[str, Any]
    """
    cmd = "show bfd session"
    try: 
        result = {}
        
        bfd_pattern = re.compile(
            r'(?m)^(?P<interface>\w+/\d+/\d+/\d+)\s+'
            r'(?P<destAddr>\d+\.\d+\.\d+\.\d+)\s+'
            r'(?P<echo>\S+\(\S+\*\d+\))\s+'
            r'(?P<async>\S+\(\S+\*\d+\))\s+'
            r'(?P<state>\S+)\s*\n\s+'
            r'(?P<hw>\S+)\s+(?P<npu>\S+)'
        )

        matches = bfd_pattern.findall(text_content)

        for match in bfd_pattern.finditer(text_content):
            interface = match.group("interface")
            entry = ShowbfdSession(
                interface=interface, 
                destAddr=match.group("destAddr"),
                localDettime=[{
                    "echo": match.group("echo"), 
                    "async": match.group("async")
                }],
                hw=match.group("hw"), 
                npu=match.group("npu"), 
                state=match.group("state")
            )
            result[interface] = asdict(entry)

        if not result: 
            return {"info": "No BFD session details found"}

        return result

    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}
    
def show_l2vpn_xconnect(text_content): 
    """
    Docstring for show_l2vpn_xconnect
    
    :param folder_path: Description
    :type folder_path: str
    :return: Description
    :rtype: Dict[str, Any]
    """
    cmd = "show l2vpn xconnect"
    try: 
        
        result = []

        xconnect_pattern = re.compile(
            r'(?ms)^(?![-\s]|Group|Name|ST|XConnect)'
            r'(?P<group>\S+)\s*\n\s+'
            r'(?P<name>\S+)\s*\n\s+'
            r'(?P<state>\S+)\s+'
            r'(?P<seg1_desc>.+?)\s+'
            r'(?P<seg1_state>\S+)\s+'
            r'(?P<seg2_desc>.+?)\s*\n\s+'
            r'(?P<seg2_state>\S+)\s*$'
        )

        matches = xconnect_pattern.finditer(text_content)

        for match in matches: 

            segments = match.groupdict()
            seg1desc = match.group('seg1_desc')
            seg2desc = match.group('seg2_desc')

            segments["seg1_desc"] = {
                "interface": seg1desc
            }
                
            if 'EVPN' in seg2desc:
                ip_regex = r'\d+\.\d+\.\d+\.\d+'

                evpn_pattern = re.compile(
                    rf'EVPN\s+(?P<evi>\d+),(?P<acId>\d+),(?P<neighborIP>{ip_regex})?\s*+'
                )

                seg2evpn = evpn_pattern.match(seg2desc)

                if seg2evpn:
                    segments['seg2_desc'] = {
                        "evi": seg2evpn.group('evi'), 
                        "acId": seg2evpn.group('acId'), 
                        "neighborIP": seg2evpn.group('neighborIP')
                    }

                entry = ShowL2VpnXconnect(
                    xonnect={
                        "group": match.group("group"), 
                        "name": match.group("name"), 
                        "state": match.group("state")
                    }, 
                    segement1={
                        "description": segments["seg1_desc"], 
                        "state": match.group("seg1_state")
                    }, 
                    segement2={
                        "description": segments["seg2_desc"], 
                        "state": match.group("seg2_state")
                    }
                )

            else: 
                segments["seg2_desc"] = {
                    "interface": seg2desc
                }

            result.append(asdict(entry))

        if not result: 
            return {"info": "l2VPN Xconnect output not found"}

        xconnectInfo = {
            "totalXconnects": len(result),
            "xonnetDetails": result
        }
        
        return xconnectInfo
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_bgp_l2vpn_evpn(text_content): 
    """
    Docstring for show_bgp_l2vpn_evpn
    
    :param folder_path: Description
    :type folder_path: str
    :return: Description
    :rtype: Dict[str, Any]
    """
    cmd = "show bgp l2vpn evpn"
    try: 
        
        if "not active" in text_content: 
            return {
                "BGP instance": "default", 
                "Status": "not active"
            }

        router_pattern = re.compile(
            r"BGP router identifier\s+(?P<routerId>\S+),\s+"
            r"local AS number\s+(?P<localAsNo>\d+)"
        )

        routerDetails = router_pattern.search(text_content)
        if routerDetails: 
            routerId = routerDetails.group("routerId")
            localASNo = routerDetails.group("localAsNo")
        rd_blocks = re.split(r'(?=^Route Distinguisher:)', text_content, flags=re.M)

        # Patterns
        rd_pattern = re.compile(r'^Route Distinguisher:\s+(\d+:\d+)(?: \(default for vrf VPWS:(\w+)\))?', re.M)
        path_pattern = re.compile(r'^([*> ]+i?\[.*?\]/\d+)', re.M)
        next_hop_pattern = re.compile(
            r'^\s*([*> ]*i?)?\s*(\d{1,3}(?:\.\d{1,3}){3})\s+(\d+)?\s+(\d+)?\s+(\w+)',
            re.M
        )
        networkInfo = []
        
        for block in rd_blocks[1:]:
            rd_match = rd_pattern.match(block)
            if not rd_match:
                continue
            routerDist, vrfVPWS = rd_match.groups()

            paths = []
            for pm in path_pattern.finditer(block):
                bestValidPath = pm.group(1)

                # Find next hops tied to this path
                next_path_match = path_pattern.search(block, pm.end())
                next_path_start = next_path_match.start() if next_path_match else len(block)

                # Slice only the text between this path and the next path
                hop_section = block[pm.end():next_path_start]
                nextHop = []
                
                nh_iter = next_hop_pattern.finditer(hop_section)
                for nh in nh_iter:
                    status_codes, ip, locPref, weight, path = nh.groups()

                    if path is "i": 
                        path = "IGP(i)"
                    elif path is "e": 
                        path = "EGP(e)"
                    else: 
                        path = path
                    
                    nextHop.append({
                        "ip": ip,
                        "status_codes": status_codes.strip() if status_codes else "",
                        "locPref": int(locPref) if locPref else None,
                        "weight": int(weight) if weight else None,
                        "path": path
                    })

                paths.append({
                    "bestValidPath": bestValidPath, 
                    "nextHop": nextHop
                })
            networkInfo.append({
                "routeDist": routerDist, 
                "vrfVPWS": vrfVPWS or "", 
                "path": paths
            })
        entry = ShowbgpL2vpnEvpn(
            routerId=routerId, 
            localASNumber=localASNo, 
            networkInfo=networkInfo
        )
        result = asdict(entry)

        if not result: 
            return {"info": "% BGP instance 'default' not active"}
          
        return result
    except Exception as e:
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_l2vpn_flexible_xconnect_service(text_content):
    cmd =  "show l2vpn flexible-xconnect-service"
    try:

        result, flexible_service = {}, []

        service_info = re.compile(
            r'^(?P<name>\S+)\s+(?P<state>\S+)', 
            re.MULTILINE
        )

        segment_pattern = re.compile(
            r"\s*(?P<segType>AC:|PW:)\s+(?P<Description>\S+.+?)(?:\s+(?P<segState>\S+))?\s*$", 
            re.MULTILINE
        )

        services = re.split(r'-{3,}', text_content)
            
        for svc in services[1:]:

            flexible_svc = service_info.search(svc)
            if not flexible_svc: 
                continue

            segm = []
            
            for seg in segment_pattern.finditer(svc): 
                segments = seg.groupdict()

                desc = seg.group('Description')

                if 'EVPN' in desc: 
                    ip_regex = r'\d+\.\d+\.\d+\.\d+'
                    
                    evpn_pattern = re.compile(
                        rf'EVPN\s+(?P<evi>\d+),(?P<target>\d+),(?P<neighborIP>{ip_regex})?\s*'
                    )

                    evpn = evpn_pattern.match(desc)
                    if evpn:
                        segments['Description'] = {
                                "neighbor": "evpn", 
                                "evi": evpn.group('evi'), 
                                "target": evpn.group('target'), 
                                "ipAddress": evpn.group('neighborIP')
                            }
                    else: 
                        segments['Description'] = {'raw': desc}
                else: 
                    segments["Description"] = {
                        "interface": desc
                    }
                segm.append(segments)
            flex_name = flexible_svc.group('name')
            entry = FlexibleXconnectService(
                name=flex_name, 
                state=flexible_svc.group('state'), 
                totalSegments=len(segm), 
                segments=segm
            )
            result[flex_name] = asdict(entry)
        
        if not result: 
            return {"info": "No flexible xonnect service found"}

        return result
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_bgp_l2vpn_evpn_advertised(text_content): 
    cmd = "show bgp l2vpn evpn advertised"
    try:

        if "not active" in text_content: 
            return {
                "BGP instance": "default", 
                "Status": "not active"
            }
        
        result = []
        bgpInfo = []
        advertised = []

        rd_pattern = re.compile(
            r'^Route Distinguisher:\s*(?P<rd>(\d+:\d+)?)', re.M
        )

        rd_blocks = re.split(r'(?=^Route Distinguisher:)', text_content, flags=re.M)

        path_pattern = re.compile(
            r'^(?P<path>\[.*?\]\/\d+)'
            r'\s*is advertised to (?P<ipAddr>\d+\d.\d+\.\d+\.\d+)$', 
            re.M
        )

        path_info_pattern = re.compile(
            r'^\s*neighbor:\s*(?P<neighbor>\S+)\s*'
            r'(neighbor router id:\s*(?P<routerID>\d+\.\d+\.\d+\.\d+))'
            r'\s*(?P<pathdesc>.*?)$', 
            re.MULTILINE
            
        )

        inbound_policy_pattern = re.compile(
            r'^\s*Attributes after inbound policy was applied:\s*\n'
            r'\s*next hop:\s*(?P<ipAddr>\d+\.\d+\.\d+\.\d+)\s*\n'
            r'(?:\s*EXTCOMM\s*\n)'
            r'\s*origin:\s*(?P<inboundOrg>\S+)\s*\n'
            r'\s*aspath:\s*(?P<inboundASPath>[^\n]*)\s*\n'
            r'\s*extended community:\s*(?P<evpnAttr>EVPN\sL2\sATTRS:[^ ]+)\s*RT:(?P<inboundRT>\d+\:\d+)',
            re.MULTILINE | re.DOTALL
        )

        outbound_policy_pattern = re.compile(
            r'^\s*Attributes after outbound policy was applied:\s*\n'
            r'\s*next hop:\s*(?P<ipAddr>\d+\.\d+\.\d+\.\d+)\s*\n'
            r'(?:\s*ORG AS EXTCOMM\s*\n)'
            r'\s*origin:\s*(?P<outboundOrg>\S+)\s*\n'
            r'\s*aspath:\s*(?P<outboundASPath>[^\n]*)\s*\n'
            r'\s*extended community:\s*(?P<evpnAttr>EVPN\sL2\sATTRS:[^ ]+)\s*RT:(?P<outboundRT>\d+\:\d+)',
            re.MULTILINE | re.DOTALL
        )
        
        for block in rd_blocks: 
            rd_match = rd_pattern.match(block)
            if not rd_match: 
                continue
            routerDist = rd_match.group('rd')
            entry = next((r for r in result if r.routerDist == routerDist), None)
            if not entry: 
                entry = ShowbgpL2vpEvpnAdvertised(
                    routerDist=routerDist, 
                    pathInfo={
                        "validPath": "", 
                        "advertisedTo": [], 
                        "neighbor": "", 
                        "routerId": "", 
                        "description": ""
                    },
                    inboundPolicy = {
                        "nextHop": "", 
                        "origin": "", 
                        "asPath": "", 
                        "extendedCommunity": {"evpnAttr": "", "rt": ""}
                    },
                    outboundPolicy = {
                        "nextHop": "", 
                        "origin": "", 
                        "asPath": "", 
                        "extendedCommunity": {"evpnAttr": "", "rt": ""}
                    }
                )
                result.append(entry)
            
            for path in path_pattern.finditer(block): 
                entry.pathInfo["validPath"] = path.group("path")
                entry.pathInfo["advertisedTo"].append(path.group("ipAddr"))
            
            pm = path_info_pattern.search(block)
            if pm: 
                entry.pathInfo["neighbor"] = pm.group('neighbor')
                entry.pathInfo["routerId"] = pm.group('routerID')
                entry.pathInfo["description"] = pm.group('pathdesc')
            
            inbound = inbound_policy_pattern.search(block)
            if inbound: 
                entry.inboundPolicy["nextHop"] = inbound.group('ipAddr')
                entry.inboundPolicy["origin"] = inbound.group('inboundOrg')
                entry.inboundPolicy["asPath"] = inbound.group('inboundASPath')
                entry.inboundPolicy["extendedCommunity"]["evpnAttr"] = inbound.group("evpnAttr")
                entry.inboundPolicy["extendedCommunity"]["rt"] = inbound.group('inboundRT')

            outbound = outbound_policy_pattern.search(block)
            if outbound: 
                entry.outboundPolicy["nextHop"] = outbound.group('ipAddr')
                entry.outboundPolicy["origin"] = outbound.group('outboundOrg')
                entry.outboundPolicy["asPath"] = outbound.group('outboundASPath')
                entry.outboundPolicy["extendedCommunity"]["evpnAttr"] = outbound.group("evpnAttr")
                entry.outboundPolicy["extendedCommunity"]["rt"] = outbound.group('outboundRT')

        for res in result: 
            bgpInfo.append(asdict(res))

        if not bgpInfo: 
            return {"info": "% BGP instance 'default' not active"}

        advertised = {
            "totalAdvertisedRoutes": len(bgpInfo), 
            "advertisedRoutes": bgpInfo   
        }    
        
        
        return advertised
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_controllers_npu_resources_all_location(text_content): 
    cmd = "show controllers npu resources all location"
    try:
        
        result = {}
        hwLocation_pattern = re.compile(
            r'^HW Resource Information For Location:\s*(?P<hwLoc>\d\/\d\/\S+)', re.M
        )
        hw_loc = re.split(r'(?=^HW Resource Information For Location:)', text_content, flags=re.M)
     
        hwInfo_pattern = re.compile(
            r'^HW Resource Information\s*\n'
            r'\s*Name\s*:\s*(?P<hwName>\S+)[\s\S]*?',
            re.M
        )

        hwUsage_pattern = re.compile(
            r'^\s+Name:\s*(?P<hwUsageName>\S+)[\s\S]*?'
            r'OOR State\s*:\s*(?P<hwUsageState>\w+)', 
            re.M
        )

        for loc in hw_loc: 
            loc_match = hwLocation_pattern.match(loc)
            
            if not loc_match: 
                continue
            location = loc_match.group('hwLoc')
            
            hwInfo = []

            # Split into HW Resource information 
            hw_block = re.split(r'(?=^HW Resource Information)', loc, flags=re.M)
            for info in hw_block: 
                hw_match = re.search(r'^HW Resource Information\s*\n\s*Name\s*:\s*(?P<hwName>\S+)', info, re.M)
                if not hw_match:
                    continue
                hw_name = hw_match.group('hwName')
                
                state_match = re.search(
                    r'OOR Summary([\s\S]*?)(?=^Current|^OFA|^HW Resource Information|\Z)',
                    info,
                    re.M
                )

                hw_state = ""
                if state_match:
                    summary_text = state_match.group(1)
                    oor_match = re.search(r'^\s*OOR State\s*:\s*(\w+)', summary_text, re.M)
                    if oor_match:
                        hw_state = oor_match.group(1)

                hw_usage = [] 
                if re.search(r'^Current Hardware Usage', info, re.M): 
                    usage_matches = hwUsage_pattern.findall(info)

                    for u_name, u_state in usage_matches: 
                        if u_name != hw_name: 
                            hw_usage.append({
                                "name": u_name, 
                                "OORState": u_state
                            })
                
                hwInfo.append({
                    "name": hw_name, 
                    "OORState": hw_state, 
                    "hwUsage": hw_usage
                })

            result = asdict(
                ShowControllersNpuResourcesAllLocation(
                    hwLocation=location, 
                    hwInfo=hwInfo
                )
            )

            if not result: 
                return {"info": "Controllers NPU resources details not found"}
                
        return result            
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}
    
def show_bfd_session_detail(text_content): 
    cmd = "show bfd session detail"
    try:

        if re.match(r'^[A-Za-z]{3}\s+[A-Za-z]{3}\s+\d+\s+\d+:\d+:\d+\.\d+\s+\w+$', text_content.strip()):
            return {"info": "No BFD sessions found", "timestamp": text_content.strip()}

        result = {}

        interface_pattern = re.compile(
            r'I\/f:\s*(?P<intf>\w+\/\d\/\d\/\d)\,\s'
            r'Location:\s*(?P<loc>\d\/\d\/\w+)', 
            re.M
        )

        intf = re.split(r'(?=^I/f:)', text_content, flags=re.M)

        state_pattern = re.compile(
            r'[\s\S]*?State:\s*(?P<state>\w+)', 
            re.M
        )

        hw_load_pattern = re.compile(
            r'[\s\S]*?H\/W Offload Info:\s*\n'
            r'H\/W Offload capability\s*:\s*(?P<capability>\w+)\,'
            r'\s*Hosted NPU\s*:\s*(?P<npu>\d\/\d\/\w+)', 
            re.M
        )

        for detail in intf: 
            intf_match = interface_pattern.match(detail)

            if not intf_match: 
                continue
            interface = intf_match.group('intf')

            loc = intf_match.group('loc')
            state = state_pattern.search(detail).group('state')
            hwInfo = hw_load_pattern.search(detail)

            entry = ShowbfdSessionDetail(
                interface=interface, 
                location=loc, 
                state=state, 
                hwOfflodInfo=hwInfo.groupdict()
            )
            result[interface] = asdict(entry)

        if not result: 
            return {"info": "No BFD sessions found"}

        return result
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}

def show_bgp_l2vpn_evpn_summary(text_content): 
    cmd = "show bgp l2vpn evpn summary"
    try:

        result = {}
        if "not active" in text_content: 
          return {
            "BGP instance": "default" ,
            "status": "not active"
          }

        routerInfo = re.search(
            r'^BGP router identifier\s*(?P<routerId>\d+\.\d+\.\d+\.\d+),'
            r'\s*local AS number\s*(?P<localAS>\d+)', 
            text_content,
            re.M
        )
        routerId = routerInfo.group('routerId')
        localAS = routerInfo.group('localAS')

        neighInfo = re.compile(
            r'(?P<IpAddr>\d+\.\d+\.\d+\.\d+)\s+'
            r'(?P<spk>\d+)\s+'
            r'(?P<AS>\d+)\s+'
            r'(?P<msgRcd>\d+)\s+'
            r'(?P<msgSent>\d+)\s+'
            r'(?P<tblVer>\d+)\s+'
            r'(?P<inq>\d+)\s+'
            r'(?P<outq>\d+)\s+'
            r'(?P<upDown>\S+)\s+'
            r'(?P<pfxrcd>\d+)'
        )

        neighbors = [
            asdict(BgpNeighbor(
                Neighbor=m[0],
                Spk=m[1],
                RemoteAS=m[2],
                MsgRcvd=m[3],
                MsgSent=m[4],
                TblVer=m[5],
                InQ=m[6],
                OutQ=m[7],
                UpDown=m[8],
                StatePfxRcd=m[9],
            ))
            for m in re.findall(neighbor_pattern, text_content)
        ]

        result = asdict(ShowBgpAllSummary(
            RouterID=router_id,
            LocalAS=local_as,
            Neighbors=neighbors
        ))

        if not result: 
            return {"info": "% BGP instance 'default' not active"}

        return result
    except Exception as e: 
        return {"error": f"Error parsing {cmd}: {str(e)}"}


