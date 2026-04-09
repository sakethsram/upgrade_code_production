"""
mock_outputs.py
Static fixtures used by MockConnection in test mode.
Keys must match exactly what execute_command sends to conn.send_command().
"""
from dataclasses import dataclass, field, asdict
@dataclass
class ShowArpNoResolveEntry:
    mac_address: str
    ip_address: str
    interface: str
    flags: str

@dataclass
class ShowArpNoResolve:
    entries: list = field(default_factory=list)
    total_entries: int = 0

@dataclass
class ShowLldpNeighborsEntry:
    local_interface: str
    parent_interface: str
    chassis_id: str
    port_info: str
    system_name: str

@dataclass
class ShowLldpNeighbors:
    entries: list = field(default_factory=list)

# ── Juniper MX204 fixtures ────────────────────────────────────
juniper_arp = """
     MAC Address       Address         Interface                Flags
     ca:fe:6a:82:88:53 10.0.0.176      lt-0/0/0.12              none
     ca:fe:6a:82:88:54 10.0.0.177      lt-0/0/0.11              none
     1c:9c:8c:f8:6c:40 10.10.11.2      ae0.111                  none
     1c:9c:8c:f8:6c:40 10.10.101.2     ae0.101                  none
     1c:9c:8c:f8:6c:40 10.10.102.2     ae0.102                  none
     1c:9c:8c:f8:6c:40 10.10.104.2     ae0.104                  none
     1c:9c:8c:f8:6c:40 10.10.105.2     ae0.105                  none
     1c:9c:8c:f8:6c:40 10.10.112.2     ae0.112                  none
     1c:9c:8c:f8:6c:40 10.10.121.2     ae0.121                  none
     1c:9c:8c:f8:6c:40 10.10.122.2     ae0.122                  none
     1c:9c:8c:f8:6c:40 10.10.123.2     ae0.123                  none
     1c:9c:8c:f8:6c:40 10.10.124.2     ae0.124                  none
     1c:9c:8c:f8:6c:40 10.10.125.2     ae0.125                  none
     1c:9c:8c:f8:6c:40 10.10.126.2     ae0.126                  none
     1c:9c:8c:f8:6c:40 10.10.127.2     ae0.127                  none
     1c:9c:8c:f8:6c:40 10.10.128.2     ae0.128                  none
     1c:9c:8c:f8:6c:40 10.10.129.2     ae0.129                  none
     1c:9c:8c:f8:6c:40 10.10.130.2     ae0.130                  none
     1c:9c:8c:f8:6c:40 10.10.201.2     ae0.201                  none
     1c:9c:8c:f8:6c:40 10.10.202.2     ae0.202                  none
     1c:9c:8c:f8:6c:40 10.10.211.6     ae0.211                  none
     1c:9c:8c:f8:6c:40 10.10.212.6     ae0.212                  none
     1c:9c:8c:f8:6c:40 10.10.214.1     ae0.412                  none
     1c:9c:8c:f8:6c:40 10.10.214.2     ae0.413                  none
     1c:9c:8c:f8:6c:40 10.31.1.2       ae0.313                  none
     c8:fe:6a:82:88:60 213.86.204.110  xe-0/0/3:0.3400          none
    Total entries: 25
"""

juniper_lldp = """
    Local Interface    Parent Interface    Chassis Id                               Port info          System Name
    xe-0/1/3           ae0                 1c:9c:8c:f8:6c:40                        513                 EFFNAT01
    xe-0/1/4           -                   80:71:1f:75:07:c0                        1069                ESLPER01
    xe-0/1/5           -                   80:71:1f:76:ef:c0                        788                 EFFPER02
    et-0/0/2           -                   84:03:28:21:68:00                        et-0/0/51           PESEFF01
    xe-0/0/1:2         ae1                 bc:0f:fe:56:90:00                        xe-0/0/4            PESEFF03
    xe-0/0/3:1         -                   c8:fe:6a:82:90:34                        656                 EFFPER01.prizmnet.colt.net
    xe-0/0/3:0         -                   c8:fe:6a:82:90:34                        658                 EFFPER01.prizmnet.colt.net
    xe-0/0/3:3         -                   c8:fe:6a:82:90:34                        661                 EFFPER01.prizmnet.colt.net
    xe-0/0/3:2         -                   c8:fe:6a:82:90:34                        669                 EFFPER01.prizmnet.colt.net
    xe-0/0/1:0         ae10                dc:77:4c:0e:a3:a6                        Ethernet1/31        ASRLLN01
    xe-0/0/0:0         ae10                dc:77:4c:0e:a3:a7                        Ethernet1/32        ASRLLN01
    fxp0               -                   ec:38:73:d6:f7:80                        584                 BLRMGN02
"""

# ── Cisco NCS5501 fixtures ────────────────────────────────────
cisco_show_version = """
        Cisco IOS XR Software, Version 7.6.2
        Copyright (c) 2013-2022 by Cisco Systems, Inc.

        Build Information:
        Built By     : ingunawa
        Built On     : Wed Aug 10 08:17:31 PDT 2022
        Built Host   : iox-ucs-047
        Workspace    : /auto/srcarchive14/prod/7.6.2/ncs5500/ws
        Version      : 7.6.2
        Location     : /opt/cisco/XR/packages/
        Label        : 7.6.2-NCS5500_762_GISO_291024

        cisco NCS-5500 () processor
        System uptime is 51 weeks 3 days 3 hours 4 minutes
"""

cisco_show_isis = """
        IS-IS COLT Level-2 adjacencies:
        System Id      Interface                SNPA           State Hold Changed  NSF IPv4 IPv6
                                                                                    BFD  BFD
        ar90.LON       Hu0/0/1/0                *PtoP*         Up    26   51w3d    Yes Up   None
        ar106.LON      Hu0/0/1/2                *PtoP*         Up    28   51w2d    Yes Up   None

        Total adjacency count: 2
"""

cisco_asr9910_pim="""
PIM neighbors in VRF default
Flag: B - Bidir capable, P - Proxy capable, DR - Designated Router,
      E - ECMP Redirect capable, S - Sticky DR Neighbor
      * indicates the neighbor created for this router

Neighbor Address             Interface              Uptime    Expires  DR pri      Flags

212.36.130.40                Bundle-Ether505        26w4d     00:01:36 1           B
212.36.130.41*               Bundle-Ether505        26w4d     00:01:22 1           (DR) B E
212.74.68.54*                TenGigE0/0/0/6/5       1y39w     00:01:22 1           B E
212.74.68.55                 TenGigE0/0/0/6/5       1y39w     00:01:37 1           (DR) B
212.74.74.98                 TenGigE0/0/0/6/9       1y39w     00:01:44 1           P
212.74.74.99*                TenGigE0/0/0/6/9       1y39w     00:01:35 1           (DR) B E
212.74.94.244*               Loopback0              2y22w     00:01:35 1           (DR) B E
193.114.177.40               Bundle-Ether501        15w3d     00:01:20 1           B
193.114.177.41*              Bundle-Ether501        15w3d     00:01:37 1           (DR) B
212.74.85.226                TenGigE0/0/0/6/2       1y30w     00:01:31 1           P
212.74.85.227*               TenGigE0/0/0/6/2       1y30w     00:01:41 1           (DR) B E
212.74.66.86                 TenGigE0/0/0/6/6       1y30w     00:01:35 1           P
212.74.66.87*                TenGigE0/0/0/6/6       1y30w     00:01:40 1           (DR) B E
212.36.132.36                HundredGigE0/0/0/0     4w4d      00:01:41 1           B
212.36.132.37*               HundredGigE0/0/0/0     4w4d      00:01:30 1           (DR) B E
212.74.68.68*                TenGigE0/0/0/7/1       1y30w     00:01:39 1           B E
212.74.68.69                 TenGigE0/0/0/7/1       1y30w     00:01:42 1           (DR) P
193.114.176.196              Bundle-Ether502        1w5d      00:01:32 1           B
193.114.176.197*             Bundle-Ether502        1w5d      00:01:30 1           (DR) B E
212.36.132.96*               HundredGigE0/0/0/1     2w6d      00:01:25 1           B E
212.36.132.97                HundredGigE0/0/0/1     2w6d      00:01:26 1           (DR) B
212.74.84.148*               TenGigE0/0/0/6/7       1y39w     00:01:29 1           B E
212.74.84.149                TenGigE0/0/0/6/7       1y39w     00:01:35 1           (DR) P
212.74.67.134                TenGigE0/0/0/7/2       1y30w     00:01:28 1           P
212.74.67.135*               TenGigE0/0/0/7/2       1y30w     00:01:17 1           (DR) B E
212.74.70.98*                TenGigE0/0/0/6/8.47    1w4d      00:01:21 1           B
212.74.70.99                 TenGigE0/0/0/6/8.47    1w4d      00:01:29 1           (DR) B
212.74.72.184*               TenGigE0/0/0/6/8.53    1w4d      00:01:36 1           B
212.74.72.185                TenGigE0/0/0/6/8.53    3d18h     00:01:29 1           (DR) B
212.36.130.46                Bundle-Ether504        6w3d      00:01:37 1           B
212.36.130.47*               Bundle-Ether504        6w3d      00:01:30 1           (DR) B E"""
cisco_asr9910_route_summary ="""Route Source                     Routes     Backup     Deleted     Memory(bytes)
local                            664        0          0           127488       
local LSPV                       1          0          0           192          
local PM                         0          1          0           192          
connected                        663        1          0           127488       
static                           369        0          0           70848        
isis COLT                        5466       24         0           1273320      
te-client                        0          0          0           0            
bgp 8220                         1103804    73         2           211944688    
dagr                             0          0          0           0            
Total                            1110967    99         2           213544216    
"""
cisco_ncs5501_route_summary ="""Route Source                     Routes     Backup     Deleted     Memory(bytes)
local                            6969        0          0           127488       
local LSPV                       6969          0          0           192          
local PM                         6969       1          0           192          
connected                        6969        1          0           127488       
static                           6969        0          0           70848        
isis COLT                        6969       24         0           1273320      
te-client                        6969          0          0           0            
bgp 8220                         6969    73         2           211944688    
dagr                             6969          0          0           0            
Total                            6969    99         2           213544216    
"""
# ── Additional Mock Variations For Parser Testing ─────────────

# ---------- ARP VARIATION 1 ----------
juniper_arp_test1 = """
     MAC Address       Address         Interface                Flags
     aa:bb:cc:11:22:33 10.1.1.1        lt-0/0/0.10             none
     aa:bb:cc:11:22:34 10.1.1.2        lt-0/0/0.11             none
     1c:9c:8c:f8:6c:40 10.10.50.2      ae0.50                  none
     1c:9c:8c:f8:6c:40 10.10.60.2      ae0.60                  none
    Total entries: 4
"""

# ---------- ARP VARIATION 2 ----------
juniper_arp_test2 = """
     MAC Address       Address         Interface                Flags
     aa:bb:cc:11:22:35 10.2.2.1        lt-0/0/0.12             none
     aa:bb:cc:11:22:36 10.2.2.2        lt-0/0/0.13             none
    Total entries: 2
"""

# ---------- LLDP VARIATION 1 ----------
juniper_lldp_test1 = """
    Local Interface    Parent Interface    Chassis Id                               Port info          System Name
    xe-0/0/0           ae0                 00:11:22:33:44:55                        101                 CORE01
    xe-0/0/1           -                   66:77:88:99:aa:bb                        102                 EDGE01
"""

# ---------- LLDP VARIATION 2 ----------
juniper_lldp_test2 = """
    Local Interface    Parent Interface    Chassis Id                               Port info          System Name
    xe-0/1/0           ae1                 cc:dd:ee:ff:00:11                        Ethernet1/1        DIST01
"""

# ---------- ROUTE SUMMARY VARIATION ----------
cisco_route_summary_test1 = """Route Source                     Routes     Backup     Deleted     Memory(bytes)
local                            500        0          0           120000
local LSPV                       1          0          0           192
local PM                         0          0          0           192
connected                        480        1          0           118000
static                           200        0          0           60000
isis COLT                        3200       10         0           900000
te-client                        0          0          0           0
bgp 8220                         800000     50         1           150000000
dagr                             0          0          0           0
Total                            803881     61         1           151198384
"""
MOCK_DATA_POST = {
    "cisco_asr9910": {
        "show route summary":  cisco_route_summary_test1,
        "show isis adjacency": cisco_show_isis,
    },
    "cisco_ncs5501": {
        "show route summary":  cisco_route_summary_test1,
        "show isis adjacency": cisco_show_isis,
    },
    "juniper_mx204": {
        "show arp no-resolve | no-more": juniper_arp_test1,
        "show lldp neighbors | no-more": juniper_lldp_test1,
    },
    "juniper_mx80": {
        "show arp no-resolve | no-more": juniper_arp_test2,
        "show lldp neighbors | no-more": juniper_lldp_test2,
    },
}
MOCK_DATA_PRE= {
    "cisco_asr9910": {
        "show route summary":  cisco_asr9910_route_summary,
        "show isis adjacency": cisco_show_isis,
    },
    "cisco_ncs5501": {
        "show route summary":  cisco_ncs5501_route_summary,
        "show isis adjacency": cisco_show_isis,
    },
    "juniper_mx204": {
        "show arp no-resolve | no-more": juniper_arp,
        "show lldp neighbors | no-more": juniper_lldp,
    },
    "juniper_mx80": {
        "show arp no-resolve | no-more": juniper_arp,
        "show lldp neighbors | no-more": juniper_lldp,
    },
}