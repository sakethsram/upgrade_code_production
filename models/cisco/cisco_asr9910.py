from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ShowbfdSession:
    interface: str
    destAddr: str
    localDettime: List[Dict[str, str]]
    hw: str
    npu: str
    state: str



@dataclass
class InterfaceMember:
    Interface: str
    Duplex: str
    Speed: str
    State: str

@dataclass
class InterfaceEntry:
    Interface: str
    AdminState: str
    LineProtocol: str
    MacAddress: str
    Description: str
    InternetAddress: str
    MTU: str
    Bandwidth: str
    LastLinkFlapped: str
    ArpTimeout: str
    MemberCount: int
    Members: List[InterfaceMember] = field(default_factory=list)

@dataclass
class PimNeighbor:
    neighborAddress: str
    isSelf: bool
    interface: str
    uptime: str
    expires: str
    drPriority: int
    isDR: bool
    flags: List[str]
    flagsRaw: str
    vrf: str = "default"  

@dataclass
class ShowPfmLocationAll:
    Node: str
    CurrentTime: str
    PFMTotal: int
    EmergencyAlert: int
    Critical: int
    Error: int
    RaisedTime: str
    SNumber: str
    FaultName: str
    Severity: str
    ProcessID: str
    DevicePath: str
    Handle: str

@dataclass
class ShowVersion:
    version: str
    model: str
    systemUptime: str

# ---------------------------------------------------------------------------
# ISIS
# ---------------------------------------------------------------------------
@dataclass
class ISISAdjacencies:
 systemID: str
 interface: str
 SNPA: str
 state: str
 hold: int
 changed: str
 NSF: str
 ipv4BFD: str
 ipv6BFD: str


# ---------------------------------------------------------------------------
# BFD
# ---------------------------------------------------------------------------
@dataclass
class BFDSession:
    interface: str
    dest_addr: str
    echo_time: str
    echo_interval: str
    echo_multiplier: str
    async_time: str
    async_interval: str
    async_multiplier: str
    state: str
    hardware: str
    npu: str


@dataclass
class ShowbfdSession:
    interface: str
    destAddr: str
    localDettime: List[Dict[str, str]]
    hw: str
    npu: str
    state: str


# ---------------------------------------------------------------------------
# Install Active Summary
# ---------------------------------------------------------------------------
@dataclass
class ShowInstallActiveSummary:
 Label: str
 AcivePackages: int
 Packages: List[str]

# ---------------------------------------------------------------------------
# Route Summary
# ---------------------------------------------------------------------------
@dataclass
class ShowRouteSummary:
    routeSource: str
    routes: int
    backup: int
    deleted: int
    memory: int


# ---------------------------------------------------------------------------
# BGP
# ---------------------------------------------------------------------------
@dataclass
class BgpProcessVersion:
    Process: str
    RcvTblVer: str
    BRibRib: str
    LabelVer: str
    ImportVer: str
    SendTblVer: str
    StandbyVer: str


@dataclass
class BgpNeighbor:
    Neighbor: str
    Spk: str
    RemoteAS: str
    MsgRcvd: str
    MsgSent: str
    TblVer: str
    InQ: str
    OutQ: str
    UpDown: str
    StatePfxRcd: str

@dataclass
class ShowBgpAllAllSummaryAF:
    AF: str                     # Address Family name (VPNv4 Unicast, IPv6 LU...)
    RouterID: str
    LocalAS: str
    TableState: str
    MainTableVersion: str
    ProcessVersions: List[BgpProcessVersion] = field(default_factory=list)
    Neighbors: List[BgpNeighbor] = field(default_factory=list)
    NeighborCount: int=0
#@dataclass
#class ShowBgpAllAllSummary:
#    
#    RouterID: str
#    LocalAS: str
#    TableState: str
#    MainTableVersion: str
#    ProcessVersions: List[Dict[str, Any]]
#    Neighbors: List[Dict[str, Any]]


@dataclass
class ShowBgpAllAllSummary:
    totalCount: int
    addressFamilies: List[ShowBgpAllAllSummaryAF]
@dataclass
class ShowBgpVrfAllSummary:
    VRF: str
    VRFState: str
    RouteDistinguisher: str
    VRFID: str
    RouterID: str
    LocalAS: str
    TableState: str
    MainTableVersion: str
    ProcessVersions: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# IPv4 Interface Brief
# ---------------------------------------------------------------------------
@dataclass
class ShowIpv4VrfAllInterfaceBrief:
    interface: str
    IPAddress: str
    status: str
    protocol: str
    VRFName: str

# ---------------------------------------------------------------------------
# MPLS LDP Neighbor
# ---------------------------------------------------------------------------
@dataclass
class ShowMplsLdpNeighbor:
    PeerLdpIdentifier: str
    RemoteTCP: str                
    LocalTCP: str                 
    MD5: str                     
    GracefulRestart: str        
    SessionState: str            
    LabelDistributionMode: str    
    Uptime: str                  
    MsgsSent: str                
    MsgsReceived: str            
    DiscoveryInterfacesIPv4: List[str]
    DiscoveryInterfacesIPv6: List[str]
    BoundIPv4Addresses: List[str]
    BoundIPv6Addresses: List[str]

# ---------------------------------------------------------------------------
# PIM Neighbor
# ---------------------------------------------------------------------------
@dataclass
class PimNeighbor:
    vrf: str
    neighborAddress: str
    isSelf: bool
    interface: str
    uptime: str
    expires: str
    drPriority: int
    isDR: bool
    flags: List[str]
    flagsRaw: str


# ---------------------------------------------------------------------------
# PFM Location
# ---------------------------------------------------------------------------
@dataclass
class ShowPfmLocationAll:
    Node: str
    CurrentTime: str
    PFMTotal: int
    EmergencyAlert: int
    Critical: int
    Error: int
    RaisedTime: str
    SNumber: str
    FaultName: str
    Severity: str
    ProcessID: str
    DevicePath: str
    Handle: str


# ---------------------------------------------------------------------------
# Processes CPU
# ---------------------------------------------------------------------------
@dataclass
class cpuSummary:
    oneMin: str
    fiveMin: str
    fifteenMin: str

@dataclass
class cpuProcess:
    pid: int
    oneMin: str
    fiveMin: str
    fifteenMin: str
    process: str

@dataclass
class ShowProcCPU:
    name: str
    summary: cpuSummary
    processes: List[cpuProcess]

# ---------------------------------------------------------------------------
# Watchdog Memory State
# ---------------------------------------------------------------------------
@dataclass
class memoryInfo:
 physicalMem: str
 freeMem: str
 memoryState: str

@dataclass
class ShowWatchdogMemoryState:
 nodeName: str
 memoryInfo: List[memoryInfo]



# ---------------------------------------------------------------------------
# Memory Summary (not required per spec but kept for completeness)
# ---------------------------------------------------------------------------
@dataclass
class ShowMemorySummary:
    node: str
    physical_total: str
    physical_available: str
    app_total: str
    app_available: str
    image: str
    bootram: str
    reserved: str
    iomem: str
    flashfsys: str
    shared_window: str


# ---------------------------------------------------------------------------
# Redundancy
# ---------------------------------------------------------------------------
@dataclass
class ShowRedundancy:
    ActiveNode: str
    StandbyNode: str
    RedundancyState: str
    RedundancyMode: str
    LastSwitchover: str


# ---------------------------------------------------------------------------
# Interfaces Description
# ---------------------------------------------------------------------------
@dataclass
class ShowInterfaceDescription:
    interface: str
    status: str
    protocol: str
    description: str


# ---------------------------------------------------------------------------
# Filesystem
# ---------------------------------------------------------------------------
@dataclass
class ShowFileSystemEntry:
    sizeBytes: int
    freeBytes: int
    fsType: str
    flags: str
    prefixesRaw: str
    prefixes: List[str]


# ---------------------------------------------------------------------------
# Interfaces (Bundle-Ether)
# ---------------------------------------------------------------------------
@dataclass
class BundleMember:
    Interface: str
    Duplex: str
    Speed: str
    State: str


@dataclass
class ShowInterfacesBundleEther:
    Interface: str
    AdminState: str
    LineProtocol: str
    MacAddress: str
    Description: str
    InternetAddress: str
    MTU: str
    Bandwidth: str
    LastLinkFlapped: str
    ArpTimeout: str
    MemberCount: int
    Members: List[BundleMember]


# ---------------------------------------------------------------------------
# MSDP Peer
# ---------------------------------------------------------------------------
@dataclass
class ShowMsdpPeer:
    PeerAddress: str
    AS: str
    State: str
    UptimeResetTime: str
    SACount: int
    ConnectionSource: str
    RPFPeer: str


# ---------------------------------------------------------------------------
# L2VPN XConnect Brief
# ---------------------------------------------------------------------------
@dataclass
class ShowL2vpnXconnectBrief:
    LikeToLike_UP: int
    LikeToLike_DOWN: int
    LikeToLike_UNR: int
    PwEther_UP: int
    PwEther_DOWN: int
    PwEther_UNR: int
    Total_UP: int
    Total_DOWN: int
    Total_UNRESOLVED: int


@dataclass
class L2vpnXconnectBriefRow:
    domain: str
    category: str
    typeName: str
    up: int
    down: int
    unresolved: int


@dataclass
class L2vpnXconnectBriefSummary:
    totalUp: int
    totalDown: int
    totalUnresolved: int


# ---------------------------------------------------------------------------
# HW Module FPD
# ---------------------------------------------------------------------------
@dataclass
class FPDEntry:
 Location: str
 CardType: str
 HWver: str
 FPDdevice: str
 ATRstatus: str
 FPDVersions: dict

@dataclass
class ShowhwModuleFPD:
 AutoUpgrade: str
 FPDs: List[FPDEntry]


# ---------------------------------------------------------------------------
# Platform
# ---------------------------------------------------------------------------
@dataclass
class ShowPlatform:
    Node: str
    Type: str
    State: str
    ConfigState: str


# ---------------------------------------------------------------------------
# Media Location
# ---------------------------------------------------------------------------
@dataclass
class MediaInfo:
 Partition: str
 Size: str
 Used: str
 Percent: str
 Avail: str

@dataclass
class ShowMedia:
 MediaLoc: str
 MediaInfo: List[MediaInfo]


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
@dataclass
class ShowVersion:
 version: str
 model: str
 systemUptime: str

