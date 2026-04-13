# upgrade.py
import re
import os
import time
import logging
import subprocess
import threading
from datetime import datetime
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from paramiko.ssh_exception import SSHException
from lib.utilities import device_results, disconnect


# ─────────────────────────────────────────────────────────────────────────────
# Upgrade class
# ─────────────────────────────────────────────────────────────────────────────

class Upgrade:

    def __init__(self, device_key: str, device: dict, accepted_vendors: list):
        self.device_key      = device_key
        self.device          = device
        self.host            = device.get("host") 	
        self.vendor          = device.get("vendor")
        self.model = device.get("model")
        self.accepted_vendor = accepted_vendors
        self.committed_pkgs = device.get("committed_pkgs")
        self.smu_committed_pkgs = device.get("smu_committed_pkgs")

    # ─────────────────────────────────────────────────────────────────────────
    # connect
    # ─────────────────────────────────────────────────────────────────────────
    def connect(self, logger):
        try:
            logger.info(f"[{self.device_key}]:: [connect] Connecting to device")
            logger.debug(
                f"[{self.device_key}]:: [connect] device_type={self.device.get('device_type')}, "
                f"username={self.device.get('username')}"
            )

            session_log_dir = os.path.join(os.getcwd(), "outputs")
            os.makedirs(session_log_dir, exist_ok=True)
            ip_clean_upgrade = self.host.replace(".", "_")
            model_clean      = str(self.device.get('model', 'unknown')).lower().replace("-", "")
            session_log_file = (
                f"{ip_clean_upgrade}_{self.vendor.lower()}_{model_clean}_{datetime.now().strftime("%Y-%m-%d")}_session.txt"
            )
            session_log_path = os.path.join(session_log_dir, session_log_file)
            logger.debug(f"[{self.device_key}]:: [connect] Session log -> {session_log_path}")
            if os.path.exists(session_log_path):
                logger.info(f"[{self.device_key}]: Session log file exists -- {session_log_path}")

            conn = ConnectHandler(
                device_type = self.device.get("device_type"),
                host        = self.host,
                username    = self.device.get("username"),
                password    = self.device.get("password"),
                session_log = session_log_path,
                session_log_file_mode = "append"
            )

            # Store into device_results so the rest of the pipeline sees it
            device_results[self.device_key]["conn"]                            = conn
            device_results[self.device_key]["upgrade"]["connect"]["status"]    = True
            device_results[self.device_key]["upgrade"]["connect"]["exception"] = ""

            logger.info(f"[{self.device_key}]:: [Upgrade.connect] Connected successfully")
            return conn

        except NetmikoTimeoutException as e:
            logger.error(f"[{self.device_key}]:: [Upgrade.connect] Timeout — {e}")
            device_results[self.device_key]["upgrade"]["connect"]["status"]    = False
            device_results[self.device_key]["upgrade"]["connect"]["exception"] = str(e)
            return None
        except NetmikoAuthenticationException as e:
            logger.error(f"[{self.device_key}]:: [Upgrade.connect] Auth failed — {e}")
            device_results[self.device_key]["upgrade"]["connect"]["status"]    = False
            device_results[self.device_key]["upgrade"]["connect"]["exception"] = str(e)
            return None
        except SSHException as e:
            logger.error(f"[{self.device_key}]:: [Upgrade.connect] SSH error — {e}")
            device_results[self.device_key]["upgrade"]["connect"]["status"]    = False
            device_results[self.device_key]["upgrade"]["connect"]["exception"] = str(e)
            return None
        except Exception as e:
            logger.error(f"[{self.device_key}]:: [Upgrade.connect] Unknown error — {e}")
            device_results[self.device_key]["upgrade"]["connect"]["status"]    = False
            device_results[self.device_key]["upgrade"]["connect"]["exception"] = str(e)
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # reconnect_and_verify
    # ─────────────────────────────────────────────────────────────────────────
    def reconnect_and_verify(self,hop_index, logger, interval = 120, max_retries=6, wait_time=30):
        logger.info(
            f"[{self.device_key}]:: [reconnect_and_verify] Starting — "
            f"hop_index={hop_index}, max_retries={max_retries}, wait_time={wait_time}s"
        )

        logger.info(f"[{self.device_key}]:: Starting ping check after reboot")

        if not self.pingDevice(logger, interval, max_wait=1800):
            raise RuntimeError(f"{self.device_key}: Device never came back after reboot")

        logger.info(f"[{self.device_key}]:: Device is reachable after reboot")

        disconnect(self.device_key, logger)          # kill stale session

        for attempt in range(max_retries):
            try:
                logger.info(f"[{self.device_key}]:: Reconnect attempt {attempt + 1}/{max_retries}")
                conn = self.connect(logger)
                if conn:
                    output = conn.send_command("show version")
                    if output:
                        logger.info(f"[{self.device_key}]:: SSH ready, got version output")

                        # ── write per-hop connect result ──────────────────────
                        if hop_index >= 0:
                            device_results[self.device_key]["upgrade"]["hops"][hop_index]["connect"].update({
                                "status":    True,
                                "attempt":   attempt + 1,
                                "exception": "",
                            })

                        return conn, output
                    else:
                        logger.warning(
                            f"[{self.device_key}]:: [reconnect_and_verify] Connection up but "
                            f"'show version' returned empty output on attempt {attempt + 1}"
                        )
                else:
                    logger.warning(
                        f"[{self.device_key}]:: [reconnect_and_verify] connect() returned None "
                        f"on attempt {attempt + 1}"
                    )

            except Exception as e:
                logger.warning(f"[{self.device_key}]:: attempt {attempt + 1} failed: {e}")

                if hop_index >= 0:
                    device_results[self.device_key]["upgrade"]["hops"][hop_index]["connect"].update({
                        "status":    False,
                        "attempt":   attempt + 1,
                        "exception": str(e),
                    })

            time.sleep(wait_time)

        # ── exhausted all retries ─────────────────────────────────────────────
        logger.error(
            f"[{self.device_key}]:: [reconnect_and_verify] All {max_retries} reconnect attempts exhausted"
        )
        if hop_index >= 0:
            device_results[self.device_key]["upgrade"]["hops"][hop_index]["connect"].update({
                "status":    False,
                "attempt":   max_retries,
                "exception": f"SSH not ready after {max_retries} retries",
            })
        raise RuntimeError(f"[{self.device_key}]:: SSH not ready after {max_retries} retries")

    # ─────────────────────────────────────────────────────────────────────────
    # imageUpgrade
    # ─────────────────────────────────────────────────────────────────────────

    def _write_hop(self,hop_index: int, update: dict):
        if hop_index >= 0:
            device_results[self.device_key]["upgrade"]["hops"][hop_index].update(update)

    def imageUpgrade(self, conn, expected_os, target_image, hop_index, logger, models, xr_committed_pkg = "", admin_committed_pkg = ""):
        logger.info(
            f"[{self.device_key}]:: [imageUpgrade] Starting — "
            f"hop_index={hop_index}, target_image={target_image}, expected_os={expected_os}"
        )

        try:
            reboot_system = True
            # ── Get current version from device_results (set by get_show_version) ──
            curr_version = device_results[self.device_key]["device_info"]["version"]
            print(f"[imageUpgrade] current version: {curr_version}")
            logger.info(f"[{self.device_key}]:: current version -> {curr_version}")
            logger.debug(
                f"[{self.device_key}]:: [imageUpgrade] Version check — "
                f"curr={curr_version}, expected={expected_os}"
            )

            if expected_os == curr_version:
                logger.info(f"[{self.device_key}]:: Already running expected version")
                self._write_hop(hop_index, {"image": f"{target_image}", "status": "already_upgraded", "exception": "", "md5_match": True})
                return conn, True

            logger.info(f"[{self.device_key}]:: Installing device image: {target_image}")

            if self.vendor == "juniper":
                cmd    = f"request vmhost software add /var/tmp/{target_image} no-validate"
                logger.debug(f"[{self.device_key}]:: [imageUpgrade] Sending: {cmd} (read_timeout=600s)")
                output = conn.send_command(cmd, read_timeout=600)
                print(f"[imageUpgrade] install output: {output}")

                if not output:
                    msg = f"{target_image} is not installed. Please check imageUpgrade()"
                    logger.error(msg)
                    self._write_hop(hop_index, {"image": f"{target_image}", "status": "failed", "exception": msg, "md5_match": False})
                    return conn, False

            if self.vendor == "cisco":
                asr_models = next(d['asr9k'] for d in models if 'asr9k' in d)
                ncs_models = next(d['ncs'] for d in models if 'ncs' in d)

                if self.model in ncs_models:
                    command = f"run mv /misc/disk1/{target_image} /misc/app_host/"

                    move_file = conn.send_command_timing(command, read_timeout=0, last_read=30)

                    if "No space left on device" in move_file:
                        msg = f"[{self.device_key}]: error writing '/misc/app_host/ncs5500-goldenk9-x-7.7.2-NCS5501_772.iso': No space left on device"
                        logger.error(msg)
                        self._write_hop(hop_index, {"image": f"{target_image}", "status": "failed", "exception": msg, "md5_match": False})
                        return conn, False

                    output=conn.send_command_timing(f"install replace /misc/app_host/{target_image} commit force noprompt",read_timeout = 0, last_read = 450)
                    logger.info(f"upgrade: {output}")

                if self.model in asr_models:

                    try:
                      cmd = "install commit"
                      logger.info(f"[{self.device_key}]: running 'install commit' to change the device state to committed state")
                      output = conn.send_command_timing(cmd, read_timeout = 0, last_read = 60)
                      logger.info(f"[{self.device_key}]:: install commit output -> {output}")

                      if not output:
                        msg = f"[{self.device_key}]: Not able to change the device state"
                        logger.error(msg)
                        return conn, False
                    except Exception as e:
                      msg = f"Not able to change the device state to committed state: {e}"
                      logger.error(msg)
                      return conn, False

                    logger.info(f"[{self.device_key}] : The device is in committed state")

                    output=conn.send_command_timing(f"install replace harddisk:/{target_image} commit noprompt",read_timeout = 0, last_read = 450)

                    logger.info(f"upgrade: {output}")
                    if not output:
                      logger.error("[{self.device_key}] Not able to run the installation commands")
                      return conn, False

                    logger.info(f"{self.device_key}: Install command accepted, router will reload automatically")

                if not output:
                    msg = f"{target_image} is not installed. Please check imageUpgrade()"
                    logger.error(msg)
                    self._write_hop(hop_index, {"image": f"{target_image}", "status": "failed", "exception": msg, "md5_match": False})
                    return conn, False



            logger.info(f"[{self.device_key}] : [imageUpgrade] Install completed, initiating reboot")
            if self.vendor == "juniper":
                command = ["request vmhost reboot", "yes", "\n"]
                logger.info(f"[{self.device_key}]:: Rebooting the system...")
                output = conn.send_multiline_timing(command)
                if not output:
                    logger.error(f"[{self.device_key}]: Not able to reboot the device")
                    reboot_system = False

            logger.info(f"[{self.device_key}]:: Waiting for reboot after upgrade")

            if reboot_system:
                logger.info(f"[{self.device_key}]:: Device rebooted, waiting for SSH to come back")
                conn, output = self.reconnect_and_verify(hop_index,logger)
                print(f"[imageUpgrade] post-reboot output: {output}")

                if self.vendor == "juniper":
                    version_pattern = re.search(r"Junos:\s*(?P<version>\S+)", output, re.IGNORECASE)
                if self.vendor == "cisco":
                    asr_models = next(d['asr9k'] for d in models if 'asr9k' in d)
                    ncs_models = next(d['ncs'] for d in models if 'ncs' in d)
                    #------ Committing the packages -----------------------#
                    try:
                      cmd = "install commit"
                      logger.info(f"[{self.device_key}]: running 'install commit' to commit the {target_image} packages")
                      output = conn.send_command_timing(cmd, read_timeout = 0, last_read = 60)
                      logger.info(f"[{self.device_key}]:: install commit output -> {output}")

                      if not output:
                        msg = f"[{self.device_key}]: Not able to commit the SMU packages"
                        logger.error(msg)
                        return conn, False
                    except Exception as e:
                      msg = f"Not able to commit the SMU packages for {smu_image}: {e}"
                      logger.error(msg)
                      return conn, False

                    if self.model in ncs_models:
                        logger.info(f"The image is upgraded. Removing the file from /misc/app_host/" )
                        remove_file = conn.send_command(f"run rm /misc/app_host/{target_image} ")

                        if not remove_file:
                            msg = f"Not able to delete the {target_image} file from /misc/app_host"
                            logger.error(msg)
                            self._write_hop(hop_index, {"image": f"{target_image}", "status": "failed", "exception": msg, "md5_match": False})

                    #-------------- Validate device version ---------------#
                    xr_match, admin_match = self.validate_upgrade(conn, xr_committed_pkg, admin_committed_pkg, logger, summary = "active")

                    if xr_match and admin_match:
                      xr_version = xr_match.group("version")
                      logger.info(f"[{self.device_key}] version in XR mode: {xr_version}")

                      admin_version = admin_match.group("version")
                      logger.info(f"[{self.device_key}] version in ADMIN mode: {admin_version}")

                      if xr_version == admin_version:
                        version_pattern = xr_match
                      else:
                        logger.error(f"[{self.device_key}]::vXR ({xr_version}) and Admin ({admin_version}) versions mismatch")
                        version_pattern = None
                    else:
                      logger.error(f"[{self.device_key}]:: version not found in xr/admin output")
                      version_pattern = None


                    #------------ Validate Commit packages ----------------------- #

                    pkg_committed = self.validate_upgrade(conn, xr_committed_pkg, admin_committed_pkg, logger)
                    if not pkg_committed:
                      msg = f"[{self.device_key}]: not found committed packages "
                      logger.error(msg)
                      self._write_hop(hop_index, {"image": f"{target_image}", "status": "failed", "exception": msg, "smu_upgrade": False})
                      return conn, False

                if version_pattern:
                    new_version = version_pattern.group("version")
                    logger.debug(
                        f"[{self.device_key}]:: [imageUpgrade] Version regex matched — new_version={new_version}"
                    )
                else:
                    msg = "No version found in show version output after reboot"
                    logger.warning(msg)
                    self._write_hop(hop_index, {"image": f"{target_image}", "status": "failed", "exception": msg, "md5_match": False})
                    raise ValueError(msg)

                # ── Update device_info version so next hop reads the right value ──
                device_results[self.device_key]["device_info"]["version"] = new_version
                logger.info(f"[{self.device_key}]:: Version information retrieved")
                logger.info(f"[{self.device_key}]:: New Version -> {new_version}")

                if expected_os == new_version:
                    logger.info(f"[{self.device_key}]:: Upgrade hop SUCCESS — {new_version}")
                    self._write_hop(hop_index, {"image": f"{target_image}", "status": "success", "exception": "", "md5_match": True})
                    return conn, True
                else:
                    msg = (
                        f"Version mismatch after upgrade — "
                        f"expected={expected_os}, got={new_version}"
                    )
                    logger.error(f"[{self.device_key}]:: {msg}")
                    self._write_hop(hop_index, {"image": f"{target_image}", "status": "failed", "exception": msg, "md5_match": False})
                    return conn, False

            else:
                logger.error(
                    f"[{self.device_key}]:: [imageUpgrade] systemReboot() returned False — "
                    f"device did not come back for image {target_image}"
                )

        except Exception as e:
            msg = f"[{self.device_key}]:: Image upgrade failed: {e}"
            logger.exception(msg)
            self._write_hop(hop_index, {"image": f"{target_image}", "status": "failed", "exception": str(e), "md5_match": False})
            return conn, False

    #------------------------------------------------------------------------------------#
    #                              Ping Device                                           #
    #------------------------------------------------------------------------------------#
    def pingDevice(self, logger, interval, max_wait, packet_size=5, count=2, timeout=2):
        logger.debug(
            f"{self.device_key}: [pingDevice] count={count}, packet_size={packet_size}, timeout={timeout}s"
        )
        try:
            command = [
                "ping",
                "-c", str(count),
                "-s", str(packet_size),
                "-W", str(timeout),
                self.host
            ]

            logger.info(f"{self.device_key}: Waiting for device via continuous ping...")
            result = 0
            while interval < max_wait :
                result = subprocess.run(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                logger.info(f"{self.device_key}: Still waiting for ping...")
                if result.returncode == 0:
                    break
                time.sleep(interval)
                interval += interval


            reachable = result.returncode == 0
            if reachable:
                logger.info(f"{self.device_key}: [pingDevice] Host is reachable (rc={result.returncode})")
            else:
                logger.warning(f"{self.device_key}: [pingDevice] Host did not respond (rc={result.returncode})")
            return reachable
        except Exception as e:
            logger.error(f"{self.device_key}: Ping failed with error: {e}")
            logger.info(f"{self.device_key}: Host is not reachable")
            return False

    #------------------------------------------------------------------------------------#
    #                              Applying DENY-ANY Policies                            #
    #------------------------------------------------------------------------------------#

    def get_asn(self, conn, logger):
        """Extract local BGP ASN"""
        try:
            output = conn.send_command_timing("show bgp summary", read_timeout = 0, last_read=30)
            match = re.search(r"local AS number (\d+)", output)
            if match:
                asn = match.group(1)
                logger.info(f"[{self.device_key}]:: Detected BGP ASN -> {asn}")
                return asn
            logger.error(f"[{self.device_key}]:: Unable to detect BGP ASN")
            return None
        except Exception as e:
            logger.exception(f"[{self.device_key}]:: Failed to retrieve ASN: {e}")
            return None

    def get_neighbors(self, conn, logger):
        """Get Colt Asia neighbors (ASN 10021)"""
        try:
            ipv4_neighbors = []
            ipv6_neighbors = []
            ipv4_output = conn.send_command_timing("show bgp summary", read_timeout = 0, last_read=30)
            ipv6_output = conn.send_command_timing("show bgp ipv6 unicast summary", read_timeout = 0, last_read=30)
            for line in ipv4_output.splitlines():
                parts = line.split()
                if parts:
                    ipv4_neighbors.append(parts[0])
            for line in ipv6_output.splitlines():
                parts = line.split()
                if parts:
                    ipv6_neighbors.append(parts[0])
            logger.info(f"[{self.device_key}]:: IPv4 neighbors detected -> {ipv4_neighbors}")
            logger.info(f"[{self.device_key}]:: IPv6 neighbors detected -> {ipv6_neighbors}")
            return ipv4_neighbors, ipv6_neighbors
        except Exception as e:
            logger.exception(f"[{self.device_key}]:: Failed to retrieve neighbors: {e}")
            return [], []

    def apply_deny_policy(self, conn, logger):
        """
        Apply `route-policy DENY-ANY in/out` to all Colt Asia neighbors
        after auto-detecting ASN and neighbors from the device.
        """
        try:
            asn = self.get_asn(conn, logger)
            if not asn:
              logger.error(f"[{self.device_key}]:: Aborting DENY-ANY apply (ASN not found)")
              return False
            ipv4_neighbors, ipv6_neighbors = self.get_neighbors(conn, logger)
            for nbr in ipv4_neighbors:
                commands = [
                    f"router bgp {asn}",
                    f"neighbor {nbr}",
                    "address-family ipv4 unicast",
                    "route-policy DENY-ANY out",
                    "route-policy DENY-ANY in"
                ]
                logger.info(f"[{self.device_key}]:: Applying DENY-ANY to IPv4 neighbor {nbr}")
                conn.send_config_set(commands, cmd_verify=False, read_timeout=60)
                conn.exit_config_mode()
            for nbr in ipv6_neighbors:
                commands = [
                    f"router bgp {asn}",
                    f"neighbor {nbr}",
                    "address-family ipv6 unicast",
                    "route-policy DENY-ANY out",
                    "route-policy DENY-ANY in"
                ]
                logger.info(f"[{self.device_key}]:: Applying DENY-ANY to IPv6 neighbor {nbr}")
                conn.send_config_set(commands, cmd_verify=False, read_timeout=60)
                conn.exit_config_mode()
            return True

        except Exception as e:
            logger.exception(f"[{self.device_key}]:: Failed to apply DENY-ANY policy: {e}")
            return False

    #------------------------------------------------------------------------------------#
    #                              Setting Overload bit                                  #
    #------------------------------------------------------------------------------------#

    def set_overload_bit(self, conn, logger, models):
        """Drain traffic before upgrade"""
        try:
            asr_models = next(d['asr9k'] for d in models if 'asr9k' in d)
            ncs_models = next(d['ncs'] for d in models if 'ncs' in d)

            if self.model in asr_models:
                policy_check = conn.send_command_timing("show running-config route-policy DENY-ANY", read_timeout = 0, last_read = 30)
                if "route-policy DENY-ANY" not in policy_check:
                    msg = "creating route-policy DENY-ANY"
                    logger.info(msg)
                    print(msg)
                    policy_commands = [
                        "route-policy DENY-ANY",
                        "drop",
                        "end-policy",
                        "commit"
                    ]
                    conn.send_config_set(policy_commands)
                    conn.exit_config_mode()
                msg="route-policy created"
                logger.info(msg)

                asn = self.get_asn(conn, logger)
                print(f"ASN->{asn}")
                logger.info(f"[{self.device_key}]:: Starting deny-any policy for ASN {asn}")
                bgp_config = conn.send_command_timing( "show running-config router bgp | include neighbor-group PEER", read_timeout = 0, last_read=30)
                if "neighbor-group PEER" in bgp_config:
                    peer_commands = [
                      f"router bgp {asn}",
                      "neighbor-group PEER",
                      "address-family ipv4 unicast",
                      "route-policy DENY-ANY out",
                      "route-policy DENY-ANY in",
                      "address-family ipv6 labeled-unicast",
                      "route-policy DENY-ANY out",
                      "route-policy DENY-ANY in",
                      "commit"
                    ]
                    conn.send_config_set(peer_commands)
                    conn.exit_config_mode()
#                    conn.send_command("commit")
                    logger.info(f"[{self.device_key}]:: Applied DENY-ANY policy to PEER group")
                    logger.info(f"[{self.device_key}]:: Waiting 5 minutes for traffic drain")
                    time.sleep(300)

            isis_commands = [
                "router isis COLT",
                "set-overload-bit",
                "commit"
            ]

            conn.send_config_set(isis_commands)
            conn.exit_config_mode()

            validateOLbit = 'sh isis instance COLT | in Overload'
            output = conn.send_command_timing(validateOLbit, read_timeout = 0, last_read = 30)
            if "configured, set" not in output:
                msg = f"ISIS Overload bit is not SET"
                logger.error(f"[{self.device_key}]: {msg}")
                return {
                  "status": "failed",
                  "exception": msg,
                  "OLBitSet": False
                }
            logger.info(f"[{self.device_key}]: ISIS overload bit set")
            return {
                "status": "OK",
                "exception": "",
                "OLBitSet": True
            }
        except Exception as e:
            logger.error(f"[{self.device_key}]: set_overload_bit failed -> {e}")
            raise


    #------------------------------------------------------------------------------------#
    #                              SMU upgrade                                       #
    #------------------------------------------------------------------------------------#
    def smu_add(self, conn, logger, smu_file): # use while loop for reload.
        """Add SMU package and extract install operation ID"""
        try:
            for attempt in range(1,6):
                cmd = f"install add source harddisk: {smu_file}"
                logger.info(f"[{self.device_key}]: Running -> {cmd} (Attempt {attempt}/5)")
                output = conn.send_command_timing(cmd, read_timeout=0, last_read=120)
                logger.debug(f"[{self.device_key}]: install add output:\n{output}")

                #  STILL IN PROGRESS / RETRY REQUIRED
                if (
                  "still in progress" in output.lower()
                  or "could not start this install operation" in output.lower()
                ):
                  logger.warning(f"[{self.device_key}]: install busy, retrying in 60s...")
                  time.sleep(60)
                  continue

                #  SUCCESS: extract install id
                match = re.search(r"Install operation\s+(\d+)\s+finished successfully", output,re.IGNORECASE)
                if match:
                  install_id = match.group(1)
                  logger.info(f"[{self.device_key}]: install add successful — ID={install_id}")
                  return True, install_id
                #  STALE PREPARE STATE → RUN prepare clean
                if "prepare operation was performed previously" in output.lower():
                  logger.warning(f"[{self.device_key}]: stale prepare detected, retrying install add")
                  time.sleep(10)
                  continue  # retry install add
                #  INVALID ID → retry
                if "invalid" in output.lower():
                  logger.warning(f"[{self.device_key}]: invalid id, retrying after 60s")
                  time.sleep(60)
                  continue
                #  Other failure
                logger.error(f"[{self.device_key}]: unexpected add error:\n{output}")
                return False, None
            msg = "Unable to detect install operation ID"
            logger.error(f"[{self.device_key}]:: Unable to detect install operation ID")
            return False, None
        except Exception as e:
            logger.exception(f"[{self.device_key}]:: SMU add failed -> {e}")
            return False, None

    def smu_prepare(self, conn, install_id, logger):
        """
        Run install prepare using install-id.
        """
        try:
            cmd = f"install prepare id {install_id}"
            logger.info(f"[{self.device_key}]: Running command -> {cmd}")

            output = conn.send_command_timing(cmd,read_timeout=0,last_read=180)

            logger.info(f"[{self.device_key}]: Prepare output -> {output}")
            return True, output

        except Exception as e:
            logger.error(f"[{self.device_key}]: SMU prepare failed -> {e}")
            return False, None

    def smu_activate(self, conn, install_id, logger, models):
        try:
            asr_models = next(d['asr9k'] for d in models if 'asr9k' in d)

            if self.model in asr_models:
              cmd = f"install activate noprompt"
            else:
              cmd = f"install activate id {install_id} noprompt"
            logger.info(f"[{self.device_key}]: Running command -> {cmd}")
            output = conn.send_command_timing(cmd, read_timeout = 0, last_read = 20)
            logger.info(f"[{self.device_key}]:: Activate output -> {output}")

            if "aborted" in output:
              logger.error(f"[{self.device_key}]: SMU activate aborted")
              return output, False
            return output, True
        except Exception as e:
            logger.error(f"[{self.device_key}]:: SMU activate failed: {e}")
            return None, False




    # --------- Running committed summary -------------------#
    def validate_upgrade(self, conn, xr_committed_pkg, admin_committed_pkg, logger, summary="committed"):

        """Validate the upgrade is successufull or not"""
        try:
            msg = f"[{self.device_key}]: Validating the device upgrade "
            logger.info(msg)
            if summary.lower() == "committed":
                logger.info(f"[{self.device_key}]: Running 'show install committed summary' in xr mode")

                xr_comm_output = conn.send_command("show install committed summary") # 1 liner

                if not xr_comm_output:
                    logger.warning(f"[{self.device_key}] Not getting output of committed summary. Please check the command")
                    return False

                retry_count = 0
                max_retries = 5
                while (
                    retry_count < max_retries
                    and (
                        "Install operation is in progress" in xr_comm_output)):
                    logger.info(
                        f"{self.device_key}: Install in progress... retry {retry_count + 1}/5 after 60s"
                    )
                    time.sleep(60)
                    xr_comm_output = conn.send_command("show install committed summary")
                    retry_count += 1

                for pkg in xr_committed_pkg:
                    if pkg in xr_comm_output:
                        logger.info(f"[{self.device_key}] : {pkg} is committed" )
                        continue

                    logger.warning(f"[{self.device_key}]: {pkg} is not committed. Upgrade is not succesfull")
                    return  False

                logger.info(f"[{self.device_key}]: Packages are committed in XR mode")

                #------admin check--------#
                logger.info(f"[{self.device_key}]: Running 'admin show install committed summary' in admin mode")


                admin_comm_output = conn.send_command(
                    "admin show install committed summary"
                )
                if not admin_comm_output:
                    msg = f"Not getting output of committed summary. Please check the command"
                    logger.warning(msg)
                    return False

                for pkg in admin_committed_pkg: # club the xr and admin
                    if pkg in admin_comm_output:
                        msg = f"[{self.device_key}] : admin {pkg} is committed"
                        logger.info(msg)
                        continue
                    logger.warning(f"admin {pkg} is not committed. Upgrade is not succesfull")
                    return  False
                logger.info(f"[{self.device_key}]: Packages are committed in Admin mode")
                return True

            if summary.lower() == "active":
                logger.info(f"[{self.device_key}]: Running 'show install active summary' in xr mode")
                xr_output = conn.send_command("show install active summary", expect_string=r"[#>]", read_timeout=120)
                if not xr_output:
                    msg = "Not getting output of active summary. Please check the command"
                    logger.warning(msg)
                    return False

                retry_count = 0
                max_retries = 5
                while (
                    retry_count < max_retries
                    and (
                        "Install operation is in progress" in xr_output)):
                    logger.info(
                        f"{self.device_key}: Install in progress... retry {retry_count + 1}/5 after 60s"
                    )
                    time.sleep(60)
                    xr_output = conn.send_command("show install active summary")
                    retry_count += 1

                xr_match = re.search(r"version\s*=\s*(?P<version>\S+)",xr_output,re.IGNORECASE)

                if not xr_match:
                    msg = f"Not able to fetch the version from 'show install active summary'. Please check the regex"
                    logger.error(msg)
                    return False

                #------admin check--------#
                logger.info(f"[{self.device_key}]: Running 'admin show install active summary' in admin mode")


                admin_output = conn.send_command(
                    "admin show install active summary", expect_string=r"[#>]", read_timeout=120
                )
                if not admin_output:
                    msg = f"Not getting output of active summary. Please check the command"
                    logger.warning(msg)
                    return False

                while (
                    retry_count < max_retries
                    and ("Install operation is in progress" in admin_output)):
                    logger.info(
                        f"{self.device_key}: Install in progress... retry {retry_count + 1}/5 after 60s"
                    )
                    time.sleep(60)
                    admin_output = conn.send_command("admin show install active summary")
                    retry_count += 1

                admin_match = re.search(r"version\s*=\s*(?P<version>\S+)",admin_output,re.IGNORECASE)
                logger.info(f"admin: {admin_match}")
                if not admin_match:
                    msg = f"Not able to fetch the version from 'show install active summary'. Please check the regex"
                    logger.error(msg)
                    return False
                return xr_match, admin_match
        except Exception as e:
            msg = f"{self.device_key}: Upgrade validation failed with error -> {e}"
            print(msg)
            logger.exception(msg)
            return False


    def upgrade_smu(self, conn, smu_image, xr_committed_pkg, admin_committed_pkg, hop_index, logger, models):
        """Full SMU upgrade workflow"""
        try:
            reboot_system = True
            msg = f"[{self.device_key}]: Starting SMU upgrade process"
            logger.info(msg)
            asr_models = next(d['asr9k'] for d in models if 'asr9k' in d)
            is_activate = True

            #------ Adding the SMU image -----------------------#
            status, install_id = self.smu_add(conn, logger, smu_image)
            if not status:
              msg = f"SMU add failed"
              logger.error(f"[{self.device_key}]: SMU add failed")
              self._write_hop(hop_index, {"image": smu_image.split(" /"), "status": "failed", "exception": msg, "md5_match": False})
              return conn, False

            # ---------------- SMU PREPARE ----------------
            if self.model in asr_models:
              if install_id:
                prep_status, prep_output = self.smu_prepare(conn, install_id, logger)
                if not prep_status:
                  logger.error(f"{self.device_key}: SMU prepare failed")
                  return conn, False
                time.sleep(15)

              if "already active" in prep_output:
                reboot_system = False
                is_activate = False
                logger.info(f"[{self.device_key}] : No Need to run the activate command as all packages are already active")

            #------ Activate the SMU image -----------------------#
            if is_activate:
              output, is_smu_activate = self.smu_activate(conn,install_id, logger, models)
              if not is_smu_activate:
                msg = f"SMU activate failed for {install_id} "
                logger.error(f"[{self.device_key}]: SMU activate failed")
                self._write_hop(hop_index, {"image": smu_image.split(" /"), "status": "failed", "exception": msg, "md5_match": False})
                return conn, False

              if "already active" in output:
                reboot_system = False


            #------------ Reload the device -----------------------#

            if reboot_system:
              #----------- Monitor the install active ---------------#
              cmd = "sh install request"
              while True:
                  output = conn.send_command(cmd, read_timeout=600)

                  if "reload" in output.lower():
                      logger.info("Device is reloading ....")
                      break
                  else:
                      logger.info("Activating packages .... ")
                      time.sleep(60)  # wait before retrying

              time.sleep(120)
              logger.info(f"[{self.device_key}]:: Device rebooting.., waiting for SSH to come back")
              conn, output = self.reconnect_and_verify(hop_index, logger)

            else:
              logger.info(f"[{self.device_key}] : Pakages are already activated. Skipping reload ...")

            #------ Committing the packages -----------------------#
            try:
              cmd = "install commit"
              logger.info(f"[{self.device_key}]: running 'install commit' to commit the SMU packages")
              output = conn.send_command_timing(cmd, read_timeout = 0, last_read = 60)
              logger.info(f"[{self.device_key}]:: install commit output -> {output}")

              if not output:
                msg = f"Not able to commit the SMU packages"
                logger.error(f"[{self.device_key}]: {msg}")
                self._write_hop(hop_index, {"image": smu_image.split(" /"), "status": "failed", "exception": msg, "md5_match": False})
                return conn, False
            except Exception as e:
              msg = f"Not able to commit the SMU packages for {smu_image}: {e}"
              logger.error(msg)
              self._write_hop(hop_index, {"image": smu_image.split(" /"), "status": "failed", "exception": str(e), "md5_match": False})
              return conn, False


            # ----------- Verfiy the SMU Upgrade --------------------#
            pkg_committed = self.validate_upgrade(conn, xr_committed_pkg, admin_committed_pkg, logger) # run 2 times seperate as xr and admin mode.
            if not pkg_committed:
              msg = f"upgrade_smu() failed"
              logger.error(f"[{self.device_key}]: {msg}")
              self._write_hop(hop_index, {"image": smu_image.split(" /"), "status": "failed", "exception": msg, "md5_match": False})
              return conn, False

            logger.info(f"[{self.device_key}]:: SMU upgrade completed successfully")
            self._write_hop(hop_index, {"image": smu_image.split(" /"), "status": "success", "exception": "", "md5_match": True})
            return conn, True
        except Exception as e:
            msg = f"[{self.device_key}]:: SMU upgrade failed with error -> {e}"
            print(msg)
            self._write_hop(hop_index, {"image": smu_image.split(" /"), "status": "failed", "exception": str(e), "md5_match": False})
            logger.exception(msg)
            return conn, False


    #------------------------------------------------------------------------------------#
    #                              Dual RE upgrade - JUNOS                               #
    #------------------------------------------------------------------------------------#

    def systemRebootDualRE(self, conn, target_re, logger):
        logger.info(f"{self.device_key}: [systemRebootDualRE] Starting — target_re={target_re}")

        try:
            reboot_cmd = f"request vmhost reboot {target_re}"
            logger.info(f"{self.device_key}: [systemRebootDualRE] Sending: {reboot_cmd}")

            reboot_output = conn.send_multiline_timing(
                [reboot_cmd, "yes"],
            )

            logger.info(f"{self.device_key}: [systemRebootDualRE] Reboot output:\n{reboot_output}")

            logger.info(
                f"{self.device_key}: [systemRebootDualRE] Sleeping 600s (10 min) "
                f"for {target_re} to come back..."
            )
            time.sleep(600)

            # Post-reboot version check — print only, full verification is in imageUpgradeDualRE STEP 3
            logger.info(f"{self.device_key}: [systemRebootDualRE] Running post-reboot version check")
            version_output = conn.send_command(
                "show version invoke-on all-routing-engines",
                read_timeout=60,
            )
            logger.info(f"{self.device_key}: [systemRebootDualRE] Version output:\n{version_output}")

            versions = self.extract_junos_versions(version_output)

            return True

        except Exception as e:
            logger.exception(f"{self.device_key}: [systemRebootDualRE] Exception: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # imageUpgradeDualRE  — MX240 / MX480 ONLY
    # ─────────────────────────────────────────────────────────────────────────
    def imageUpgradeDualRE(self, conn, expected_os, target_image, target_re, hop_index, logger):
        logger.info(
            f"{self.device_key}: [imageUpgradeDualRE] Starting — "
            f"target_re={target_re}, hop_index={hop_index}, "
            f"target_image={target_image}, expected_os={expected_os}"
        )

        def _write_re(update: dict):
            if hop_index >= 0:
                device_results[self.device_key]["upgrade"]["hops"][hop_index][target_re].update(update)

        try:

            versions = self.extract_junos_versions(conn.send_command("show version invoke-on all-routing-engines", read_timeout=60))
            if versions.get(target_re) == expected_os:
                logger.info(f"{self.device_key}: [imageUpgradeDualRE] SKIP — {target_re} already on {expected_os}"); _write_re({"status": "success", "exception": "", "version": expected_os}); return conn, True
            # ─────────────────────────────────────────────────────────────────
            # STEP 1 — Install image on target RE
            # read_timeout=900 (15 minutes)
            # ─────────────────────────────────────────────────────────────────
            logger.info(f"{self.device_key}: [imageUpgradeDualRE] STEP 1 — Installing {target_image} on {target_re}")
            cmd = f"request vmhost software add /var/tmp/{target_image} {target_re} no-validate"
            logger.info(f"{self.device_key}: [imageUpgradeDualRE] Sending command: {cmd}")
            logger.info(f"{self.device_key}: [imageUpgradeDualRE] Waiting up to 15 minutes for install to complete...")

            output = conn.send_command(cmd, read_timeout=900, expect_string=r".*>")

            logger.info(f"{self.device_key}: [imageUpgradeDualRE] ─────────────── INSTALL OUTPUT ({target_re}) ───────────────")
            logger.info(f"\n{output}")
            logger.info(f"{self.device_key}: [imageUpgradeDualRE] ────────────────────────────────────────────────────────────")

            if not output:
                msg = f"Install returned no output for {target_image} on {target_re}"
                logger.error(f"{self.device_key}: [imageUpgradeDualRE] {msg}")
                _write_re({"status": "failed", "exception": msg, "version": ""})
                return conn, False

            # ─────────────────────────────────────────────────────────────────
            # STEP 2 — Reboot target RE, wait 10 minutes
            # ─────────────────────────────────────────────────────────────────
            reboot_ok = self.systemRebootDualRE(conn, target_re, logger)
            if not reboot_ok:
                msg = f"systemRebootDualRE failed for {target_re}"
                logger.error(f"{self.device_key}: [imageUpgradeDualRE] {msg}")
                _write_re({"status": "failed", "exception": msg, "version": ""})
                return conn, False

            # ─────────────────────────────────────────────────────────────────
            # STEP 3 — Verify: show version invoke-on all-routing-engines
            # Parse and confirm target_re is now on expected_os
            # ─────────────────────────────────────────────────────────────────
            logger.info(f"{self.device_key}: [imageUpgradeDualRE] STEP 3 — Verifying versions on all REs after {target_re} reboot")

            version_output = conn.send_command(
                "show version invoke-on all-routing-engines",
                read_timeout=60,
            )

            logger.info(f"{self.device_key}: [imageUpgradeDualRE] Version output:\n{version_output}")

            versions = self.extract_junos_versions(version_output)

            actual_version = versions.get(target_re)

            if actual_version != expected_os:
                msg = (
                    f"Version mismatch after install+reboot on {target_re} — "
                    f"expected={expected_os}, got={actual_version}"
                )
                logger.error(f"{self.device_key}: [imageUpgradeDualRE] STEP 3 FAILED — {msg}")
                _write_re({"status": "failed", "exception": msg, "version": actual_version or ""})
                return conn, False

            logger.info(
                f"{self.device_key}: [imageUpgradeDualRE] STEP 3 OK — "
                f"{target_re} confirmed at expected_os={expected_os}"
            )
            _write_re({"status": "success", "exception": "", "version": actual_version})
            return conn, True

        except Exception as e:
            msg = f"Unhandled exception: {e}"
            logger.exception(f"{self.device_key}: [imageUpgradeDualRE] {msg}")
            _write_re({"status": "failed", "exception": str(e), "version": ""})
            return conn, False

    def switchoverMaster(self, conn, hop_index, expected_new_master, logger):
        logger.info(
            f"{self.device_key}: [switchoverMaster] Starting — "
            f"hop_index={hop_index}, expected_new_master={expected_new_master}"
        )

        try:
            # ── STEP 1: Send the switchover command ───────────────────────────
            # Device will respond with a confirmation prompt before acting.
            logger.info(
                f"{self.device_key}: [switchoverMaster] STEP 1 — "
                f"Sending: request chassis routing-engine master switch"
            )
            try:
                conn.send_command(
                    "request chassis routing-engine master switch",
                    expect_string=r".*",
                    read_timeout=10,
                )
                logger.info(f"{self.device_key}: [switchoverMaster] STEP 1 — command sent, got prompt response")
            except Exception as send_err:
                logger.info(
                    f"{self.device_key}: [switchoverMaster] STEP 1 — "
                    f"expected disruption after switch command: {send_err}"
                )

            # ── STEP 2: Wait 5 s → first "yes" ───────────────────────────────
            logger.info(f"{self.device_key}: [switchoverMaster] STEP 2 — Waiting 5s, sending first 'yes'")
            time.sleep(5)
            try:
                conn.send_command("yes", expect_string=r".*", read_timeout=15)
                logger.info(f"{self.device_key}: [switchoverMaster] STEP 2 — first 'yes' sent")
            except Exception as y1_err:
                logger.info(
                    f"{self.device_key}: [switchoverMaster] STEP 2 — "
                    f"first 'yes' may have dropped (expected): {y1_err}"
                )

            # ── STEP 3: Wait 5 s → second "yes" ──────────────────────────────
            logger.info(f"{self.device_key}: [switchoverMaster] STEP 3 — Waiting 5s, sending second 'yes'")
            time.sleep(5)
            try:
                conn.send_command("yes", expect_string=r".*", read_timeout=15)
                logger.info(f"{self.device_key}: [switchoverMaster] STEP 3 — second 'yes' sent")
            except Exception as y2_err:
                logger.info(
                    f"{self.device_key}: [switchoverMaster] STEP 3 — "
                    f"second 'yes' may have dropped (expected): {y2_err}"
                )

            # ── STEP 4: Wait 15 s for the new master to take over ─────────────
            logger.info(
                f"{self.device_key}: [switchoverMaster] STEP 4 — "
                f"Waiting 13s for new master to take over"
            )
            time.sleep(15)

            # ── STEP 5: Reconnect using connect() from utilities ──────────────
            # The device does not reboot — reconnect to the same host directly.
            logger.info(f"{self.device_key}: [switchoverMaster] STEP 5 — Reconnecting to {self.host}")
            disconnect(self.device_key, logger)
            new_conn = self.connect(logger)
            if not new_conn:
                msg = "Reconnect after switchover returned None"
                logger.error(f"[{self.device_key}]: [switchoverMaster] {msg}")
                return conn, False
            logger.info(f"[{self.device_key}]: [switchoverMaster] STEP 5 — Reconnected successfully")

            # ── STEP 6: Verify new master via show chassis routing-engine ──────
            logger.info(f"[{self.device_key}]: [switchoverMaster] STEP 6 — Verifying chassis state")
            chassis_output = new_conn.send_command(
                "show chassis routing-engine",
                expect_string=r".*>",
                read_timeout=60,
            )
            logger.info(f"[{self.device_key}]: [switchoverMaster] chassis output:\n{chassis_output}")

            expected_slot = expected_new_master.replace("re", "").strip()
            master_match  = re.search(
                rf"Slot\s+{expected_slot}.*?Current state\s+Master",
                chassis_output,
                re.IGNORECASE | re.DOTALL,
            )

            if not master_match:
                re0_state = re.search(
                    r"Slot\s+0.*?Current state\s+(\S+)", chassis_output,
                    re.IGNORECASE | re.DOTALL,
                )
                re1_state = re.search(
                    r"Slot\s+1.*?Current state\s+(\S+)", chassis_output,
                    re.IGNORECASE | re.DOTALL,
                )
                msg = (
                    f"Switchover verification FAILED — expected {expected_new_master}=Master. "
                    f"Got RE0={re0_state.group(1) if re0_state else 'unknown'}, "
                    f"RE1={re1_state.group(1) if re1_state else 'unknown'}"
                )
                logger.error(f"[{self.device_key}]: [switchoverMaster] {msg}")
                return new_conn, False

            logger.info(
                f"[{self.device_key}]: [switchoverMaster] STEP 6 OK — "
                f"{expected_new_master} confirmed as Master"
            )
            return new_conn, True

        except Exception as e:
            logger.exception(f"[{self.device_key}]: [switchoverMaster] Unhandled exception: {e}")
            return conn, False


    def run_upgrade_dualRE(self, conn, image_details, curr_os, curr_image, logger):
        device_results[self.device_key]["upgrade"]["status"] = "in_progress"

        logger.info(f"[{self.device_key}] PRE-FLIGHT — Checking chassis routing-engine state")

        try:
            preflight_output = conn.send_command(
                "show chassis routing-engine",
                expect_string=r".*>",
                read_timeout=60,
            )
            logger.info(f"[{self.device_key}] PRE-FLIGHT chassis output:\n{preflight_output}")

            re0_master = re.search(
                r"Slot\s+0.*?Current state\s+Master",
                preflight_output,
                re.IGNORECASE | re.DOTALL,
            )
            re1_backup = re.search(
                r"Slot\s+1.*?Current state\s+Backup",
                preflight_output,
                re.IGNORECASE | re.DOTALL,
            )

            if not (re0_master and re1_backup):
                re0_state = re.search(r"Slot\s+0.*?Current state\s+(\S+)", preflight_output, re.IGNORECASE | re.DOTALL)
                re1_state = re.search(r"Slot\s+1.*?Current state\s+(\S+)", preflight_output, re.IGNORECASE | re.DOTALL)
                msg = (
                    f"PRE-FLIGHT FAILED — Expected RE0=Master, RE1=Backup. "
                    f"Got RE0={re0_state.group(1) if re0_state else 'unknown'}, "
                    f"RE1={re1_state.group(1) if re1_state else 'unknown'}"
                )
                logger.error(f"[{self.device_key}] {msg}")
                device_results[self.device_key]["upgrade"]["status"]    = "failed"
                device_results[self.device_key]["upgrade"]["exception"] = msg
                return conn, False

            logger.info(f"[{self.device_key}] PRE-FLIGHT OK — RE0=Master, RE1=Backup")

            # ── CHANGE 1: Capture pre-upgrade versions of both REs and store them ──
            ver_output_pre = conn.send_command(
                "show version invoke-on all-routing-engines", read_timeout=60
            )
            pre_versions = self.extract_junos_versions(ver_output_pre)
            device_results[self.device_key]["upgrade"]["pre_versions"] = pre_versions
            logger.info(f"[{self.device_key}] Pre-upgrade RE versions: {pre_versions}")

        except Exception as e:
            msg = f"PRE-FLIGHT chassis check exception: {e}"
            logger.exception(f"[{self.device_key}] {msg}")
            device_results[self.device_key]["upgrade"]["status"]    = "failed"
            device_results[self.device_key]["upgrade"]["exception"] = msg
            return conn, False

        # ─────────────────────────────────────────────────────────────────────────
        # HOP LOOP
        # ─────────────────────────────────────────────────────────────────────────
        for hop_idx, img_entry in enumerate(image_details):
            image       = img_entry.get("image")
            expected_os = img_entry.get("expected_os")
            checksum    = img_entry.get("checksum")

            logger.info(
                f"[{self.device_key}] ════════ HOP [{hop_idx}] START ════════ "
                f"image={image}, expected_os={expected_os}"
            )

            if not (image and expected_os and checksum):
                msg = f"HOP [{hop_idx}] missing required fields (image/expected_os/checksum)"
                logger.error(f"[{self.device_key}] {msg}")
                device_results[self.device_key]["upgrade"]["status"]    = "failed"
                device_results[self.device_key]["upgrade"]["exception"] = msg
                return conn, False

            try:
                logger.info(f"[{self.device_key}] ┌─ HOP [{hop_idx}] ACT 1 START @ {datetime.now().strftime('%H:%M:%S')} ─────────────────────")
                logger.info(f"[{self.device_key}] │  Target  : RE1 (Backup)")
                logger.info(f"[{self.device_key}] │  Image   : {image}")
                logger.info(f"[{self.device_key}] │  Action  : install → reboot RE1 (10 min wait) → verify version")
                logger.info(f"[{self.device_key}] │  Expect  : RE0=Master/{curr_os}  RE1=Backup/{expected_os}")

                conn, ok = self.imageUpgradeDualRE(conn, expected_os, image, "re1", hop_idx, logger)
                if not ok:
                    msg = (
                        f"HOP [{hop_idx}] ACT 1 FAILED — "
                        f"RE1 install/reboot/verify did not complete successfully "
                        f"(image={image}, expected_os={expected_os})"
                    )
                    logger.error(f"[{self.device_key}] └─ ACT 1 FAILED  ── {msg}")
                    device_results[self.device_key]["upgrade"]["status"]    = "failed"
                    device_results[self.device_key]["upgrade"]["exception"] = msg
                    device_results[self.device_key]["upgrade"]["hops"][hop_idx]["status"] = "failed"
                    return conn, False

                logger.info(f"[{self.device_key}] │  VERIFY OK: RE1={expected_os}  RE0={curr_os}  (RE0 still Master)")
                logger.info(f"[{self.device_key}] └─ HOP [{hop_idx}] ACT 1 COMPLETE @ {datetime.now().strftime('%H:%M:%S')} ────────────────────")

                logger.info(f"[{self.device_key}] ┌─ HOP [{hop_idx}] ACT 2 START @ {datetime.now().strftime('%H:%M:%S')} ─────────────────────")
                logger.info(f"[{self.device_key}] │  Action  : switchover RE0→RE1 (RE1 becomes Master)")

                conn, switchover_ok = self.switchoverMaster(
                    conn, hop_idx, expected_new_master="re1", logger=logger
                )
                if not switchover_ok:
                    msg = (
                        f"HOP [{hop_idx}] ACT 2 FAILED — "
                        f"Switchover RE0→RE1 did not complete or RE1 not confirmed as Master"
                    )
                    logger.error(f"[{self.device_key}] └─ ACT 2 FAILED  ── {msg}")
                    device_results[self.device_key]["upgrade"]["status"]    = "failed"
                    device_results[self.device_key]["upgrade"]["exception"] = msg
                    device_results[self.device_key]["upgrade"]["hops"][hop_idx]["status"] = "failed"
                    return conn, False

                # ── CHANGE 2: Record first switchover (RE0→RE1) in the hop ──
                device_results[self.device_key]["upgrade"]["hops"][hop_idx]["switchover_1"] = "RE0(M)→RE1(M)"
                logger.info(f"[{self.device_key}] │  VERIFY OK: RE1=Master  RE0=Backup  (chassis state confirmed)")
                logger.info(f"[{self.device_key}] └─ HOP [{hop_idx}] ACT 2 COMPLETE @ {datetime.now().strftime('%H:%M:%S')} ────────────────────")

                logger.info(f"[{self.device_key}] ┌─ HOP [{hop_idx}] ACT 3 START @ {datetime.now().strftime('%H:%M:%S')} ─────────────────────")
                logger.info(f"[{self.device_key}] │  Target  : RE0 (Backup)")
                logger.info(f"[{self.device_key}] │  Image   : {image}")
                logger.info(f"[{self.device_key}] │  Action  : install → reboot RE0 (10 min wait) → verify version")

                conn, ok = self.imageUpgradeDualRE(conn, expected_os, image, "re0", hop_idx, logger)
                if not ok:
                    msg = (
                        f"HOP [{hop_idx}] ACT 3 FAILED — "
                        f"RE0 install/reboot/verify did not complete successfully "
                        f"(image={image}, expected_os={expected_os})"
                    )
                    logger.error(f"[{self.device_key}] └─ ACT 3 FAILED  ── {msg}")
                    device_results[self.device_key]["upgrade"]["status"]    = "failed"
                    device_results[self.device_key]["upgrade"]["exception"] = msg
                    device_results[self.device_key]["upgrade"]["hops"][hop_idx]["status"] = "failed"
                    return conn, False

                logger.info(f"[{self.device_key}] │  VERIFY OK: RE0={expected_os}  RE1={expected_os}  (RE1 still Master)")
                logger.info(f"[{self.device_key}] └─ HOP [{hop_idx}] ACT 3 COMPLETE @ {datetime.now().strftime('%H:%M:%S')} ────────────────────")

                logger.info(f"[{self.device_key}] ┌─ HOP [{hop_idx}] ACT 4 START @ {datetime.now().strftime('%H:%M:%S')} ─────────────────────")
                logger.info(f"[{self.device_key}] │  Action  : switchover RE1→RE0 (RE0 restored as Master)")

                conn, switchover_ok = self.switchoverMaster(
                    conn, hop_idx, expected_new_master="re0", logger=logger
                )
                if not switchover_ok:
                    msg = (
                        f"HOP [{hop_idx}] ACT 4 FAILED — "
                        f"Switchover RE1→RE0 did not complete or RE0 not confirmed as Master"
                    )
                    logger.error(f"[{self.device_key}] └─ ACT 4 FAILED  ── {msg}")
                    device_results[self.device_key]["upgrade"]["status"]    = "failed"
                    device_results[self.device_key]["upgrade"]["exception"] = msg
                    device_results[self.device_key]["upgrade"]["hops"][hop_idx]["status"] = "failed"
                    return conn, False

                # ── CHANGE 3: Record second switchover (RE1→RE0) in the hop ──
                device_results[self.device_key]["upgrade"]["hops"][hop_idx]["switchover_2"] = "RE1(M)→RE0(M)"
                logger.info(f"[{self.device_key}] │  VERIFY OK: RE0=Master  RE1=Backup  (chassis state confirmed)")
                logger.info(f"[{self.device_key}] └─ HOP [{hop_idx}] ACT 4 COMPLETE @ {datetime.now().strftime('%H:%M:%S')} ────────────────────")

                # All 4 ACTs passed — mark this hop as successful
                device_results[self.device_key]["upgrade"]["hops"][hop_idx]["status"] = "success"

                # ── CHANGE 4: Capture post-hop versions of both REs ──
                ver_output_post = conn.send_command(
                    "show version invoke-on all-routing-engines", read_timeout=60
                )
                post_versions = self.extract_junos_versions(ver_output_post)
                device_results[self.device_key]["upgrade"]["hops"][hop_idx]["post_versions"] = post_versions
                logger.info(f"[{self.device_key}] Post-hop [{hop_idx}] RE versions: {post_versions}")

                # Update baseline for next hop
                curr_image = image
                curr_os    = expected_os
                logger.info(
                    f"[{self.device_key}] ════════ HOP [{hop_idx}] COMPLETE @ {datetime.now().strftime('%H:%M:%S')} ════════ "
                    f"RE0=Master/{curr_os}  RE1=Backup/{curr_os}  (both REs upgraded)"
                )

            except Exception as e:
                msg = f"HOP [{hop_idx}] unhandled exception: {e}"
                logger.exception(f"[{self.device_key}] {msg}")
                device_results[self.device_key]["upgrade"]["status"]    = "failed"
                device_results[self.device_key]["upgrade"]["exception"] = msg
                return conn, False

        # ─────────────────────────────────────────────────────────────────────────
        # ALL HOPS COMPLETE
        # ─────────────────────────────────────────────────────────────────────────
        logger.info(
            f"[{self.device_key}] DualRE Upgrade COMPLETE — "
            f"All hops done, both REs at {curr_os}, RE0=Master"
        )
        device_results[self.device_key]["upgrade"]["status"]    = "success"
        device_results[self.device_key]["upgrade"]["exception"] = ""
        return conn, True

    # ─────────────────────────────────────────────────────────────────────────────
    # extract_junos_versions
    # ─────────────────────────────────────────────────────────────────────────────
    def extract_junos_versions(self, text):
        """
        Extract Junos versions for re0 and re1 from show version invoke-on all-routing-engines output.
        Looks up to 4 lines after "re0:" / "re1:" for a line starting with "Junos:".
        Returns dict: {"re0": version_string_or_None, "re1": version_string_or_None}
        """
        lines  = text.splitlines()
        result = {"re0": None, "re1": None}

        for re_label in ["re0:", "re1:"]:
            for i, line in enumerate(lines):
                if line.strip() == re_label:
                    for look_ahead in range(1, 5):   # check up to 4 lines ahead
                        if i + look_ahead < len(lines):
                            candidate = lines[i + look_ahead].strip()
                            if candidate.lower().startswith("junos:"):
                                version = candidate.split(":", 1)[1].strip()
                                result[re_label[:-1]] = version
                                break
                    break

