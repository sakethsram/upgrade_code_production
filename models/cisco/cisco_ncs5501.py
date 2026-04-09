from dataclasses import dataclass, asdict, field
from typing import List,Optional,Dict,Any
#  OOPS CONCEPT
@dataclass
class ShowInventory:
 NAME: str 
 DESCR: str 
 PID: str
 VID: str 
 SN: str

@dataclass 
class ShowInstallActiveSummary: 
 Label: str
 AcivePackages: int 
 Packages: List[str]

@dataclass 
class ShowPlatform: 
 Node: str 
 Type: str
 State: str 
 ConfigState: str

@dataclass
class ShowInstallCommittedSummary:
 Label: str 
 CommittedPackages: int 
 Packages: List[str]


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

@dataclass
class ShowRouteSummary: 
 routeSource: str 
 routes: int 
 backup: int 
 deleted: int 
 memory: str

@dataclass
class memoryInfo:
 physicalMem: str
 freeMem: str
 memoryState: str

@dataclass
class ShowWatchdogMemoryState:
 nodeName: str
 memoryInfo: List[memoryInfo]

@dataclass
class ShowIpv4VrfAllInterfaceBrief:
    interface: str
    IPAddress: str
    status: str
    protocol: str
    VRFName: str

@dataclass
class lldpNeighbors:
    deviceId: str
    localIntf: str
    holdTime: int
    capability: str
    portId: str

@dataclass
class ShowLLDPNeighbors:
    totalEntriesDisplayed: int
    neighbors: List[lldpNeighbors]

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

@dataclass
class ShowInterfaceDescription:
    interface: str
    status: str
    protocol: str
    description: str

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

@dataclass 
class ForwardingEntries: 
    labelSwitching: int
    labelSwitchingProtected: int
    labelSwitchingReady: int
    labelSwitchingActive: int
    mplsTETunnellHead: int
    mplsTETunnellHeadProtected: int


@dataclass 
class LabelsInUse: 
    reserved: int 
    lowest: int 
    highest: int 
    deletedStaleLabelEntries: int 

@dataclass
class ForwardingUpdates: 
    messages: int 
    p2pUpdates: int 

@dataclass
class XconnectInfo: 
 numberofXconnect: int 
 up: int 
 down: int 

@dataclass
class m2mpXconnectsInfo: 
 m2mpXconnections: int 
 up: int 
 down: int 

@dataclass
class Showl2vpnXconnectSummary: 
 numberOfGroups: int 
 xconnect: dict
 adminDownSegments: int 
 m2mpXconnects: dict 
 ceConnections: dict

@dataclass
class ShowVersion: 
 version: str 
 model: str
 systemUptime: str 

@dataclass
class ShowProcessCPU: 
 oneMinUtilization: str
 fiveMinUtilization: str
 fifteenMinUtilization: str

@dataclass
class ShowbfdSession: 
 interface: str 
 destAddr: str 
 localDettime: list
 hw: str 
 npu: str 
 state: str

@dataclass
class ShowL2VpnXconnect: 
 xonnect: dict 
 segement1: dict 
 segement2: dict


@dataclass
class ShowbgpL2vpnEvpn: 
 routerId: str 
 localASNumber: int 
 networkInfo: list

@dataclass
class FlexibleXconnectService: 
 name: str 
 state: str
 totalSegments: int 
 segments: list

@dataclass
class ShowbgpL2vpEvpnAdvertised: 
 routerDist: str
 pathInfo: dict 
 inboundPolicy: dict 
 outboundPolicy: dict


@dataclass
class ShowControllersNpuResourcesAllLocation: 
 hwLocation: str 
 hwInfo: list 

@dataclass
class ShowbfdSessionDetail: 
 interface: str 
 location: str 
 state: str 
 hwOfflodInfo: dict

@dataclass
class ShowBgpAllSummary:
    RouterID: str
    LocalAS: str
    Neighbors: List[Dict[str, Any]]
