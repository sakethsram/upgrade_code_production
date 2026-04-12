import re
import time
from lib.utilities import *
import subprocess


# ─────────────────────────────────────────────────────────────────────────────
# PreCheck class
# ─────────────────────────────────────────────────────────────────────────────
class PreCheck:
    """
    Handles pre-upgrade checks: storage, disk backup, config backup, image transfer.
    Supports vendors defined in deviceDetails.yaml → accepted_vendors.
    conn and logger are always passed in from run_device_pipeline().
    """

    def __init__(self, device, device_key):
        self.device          = device
        self.host            = device.get("host")
        self.device_type     = device.get("device_type")
        self.vendor          = device.get("vendor").lower()
        self.model           = device.get("model").lower()
        self.username        = device.get("username")
        self.remote_server   = device.get("remote_backup_server")
        self.remote_password = device.get("remote_password")
        self.min_disk_gb     = device.get("min_disk_gb")
        self.device_key      = device_key
        self.accepted_vendors = device.get("accepted_vendors", [])

    #---────────────────────────────────────────────────────────────────────
    # pingDevice
    # ─────────────────────────────────────────────────────────────────────────
    def preBackupDiskDualRE(self, conn, logger):
        try:
            logger.info(f"[{self.device_key}] preBackupDiskDualRE  — vendor: {self.vendor}")

            logger.info(f"[{self.device_key}] preBackupDiskDualRE — running request system snapshot")
            snapshot_output = conn.send_command(
                "request system snapshot",
                expect_string=r'.*>',
                read_timeout=900,
            )
            logger.info(
                f"[{self.device_key}] preBackupDiskDualRE — snapshot output:\n{snapshot_output}"
            )

            if "NOTICE: Snapshot" not in snapshot_output:
                msg = (
                    f"[{self.device_key}] preBackupDiskDualRE — Gate A failed: "
                    f"'NOTICE: Snapshot' not found in snapshot command output"
                )
                logger.error(msg)
                return {
                    "status":        "failed",
                    "exception":     msg,
                    "verified":      False,
                    "snapshot_name": "",
                    "creation_date": "",
                    "junos_version": "",
                    "remark":        "Snapshot command ran but NOTICE string not found in output",
                }

            snap_name_from_cmd = ""
            m = re.search(r"NOTICE:\s+Snapshot\s+(\S+)\s+created successfully", snapshot_output)
            if m:
                snap_name_from_cmd = m.group(1)
                logger.info(
                    f"[{self.device_key}] preBackupDiskDualRE — Gate A snapshot name: "
                    f"{snap_name_from_cmd}"
                )

            logger.info(f"[{self.device_key}] preBackupDiskDualRE — running show system snapshot")
            verify_output = conn.send_command(
                "show system snapshot",
                expect_string=r'.*>',
                read_timeout=60,
            )
            logger.info(
                f"[{self.device_key}] preBackupDiskDualRE — show system snapshot output:\n"
                f"{verify_output}"
            )

            if "Configuration: yes" not in verify_output:
                msg = (
                    f"[{self.device_key}] preBackupDiskDualRE — Gate B failed: "
                    f"'Configuration: yes' not found in show system snapshot output"
                )
                logger.error(msg)
                return {
                    "status":        "failed",
                    "exception":     msg,
                    "verified":      False,
                    "snapshot_name": snap_name_from_cmd,
                    "creation_date": "",
                    "junos_version": "",
                    "remark":        f"Snapshot {snap_name_from_cmd} created but 'Configuration: yes' not confirmed",
                }

            snapshot_name = snap_name_from_cmd
            m = re.search(r"Snapshot\s+(snap\.\S+?):", verify_output)
            if m:
                snapshot_name = m.group(1)

            creation_date = ""
            m = re.search(r"Creation date:\s+(.+)", verify_output)
            if m:
                creation_date = m.group(1).strip()

            junos_version = ""
            m = re.search(r"Junos version:\s+(\S+)", verify_output)
            if m:
                junos_version = m.group(1).strip()

            logger.info(
                f"[{self.device_key}] preBackupDiskDualRE — both gates passed: "
                f"snapshot_name={snapshot_name}, creation_date={creation_date}, "
                f"junos_version={junos_version}"
            )

            return {
                "status":        "ok",
                "exception":     "",
                "verified":      True,
                "snapshot_name": snapshot_name,
                "creation_date": creation_date,
                "junos_version": junos_version,
                "remark":        f"Snapshot {snapshot_name} verified — JunOS {junos_version} ({creation_date})",
            }

        except Exception as e:
            msg = f"[{self.device_key}] preBackupDiskDualRE failed: {e}"
            logger.error(msg)
            return {
                "status":        "failed",
                "exception":     str(e),
                "verified":      False,
                "snapshot_name": "",
                "creation_date": "",
                "junos_version": "",
                "remark":        f"Exception during snapshot: {str(e)[:80]}",
            }
    def pingDevice(self, logger, interval, max_wait, packet_size=5, count=2, timeout=2):
        logger.debug(
            f"{self.host}: [pingDevice] count={count}, packet_size={packet_size}, timeout={timeout}s"
        )
        try:
            command = [
                "ping",
                "-c", str(count),
                "-s", str(packet_size),
                "-W", str(timeout),
                self.host
            ]

            logger.info(f"{self.host}: Waiting for device via continuous ping...")
            result = 0
            while True:
                result = subprocess.run(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                logger.info(f"{self.host}: Still waiting for ping...")
                if result.returncode == 0:
                    break
                time.sleep(interval)
                interval += interval


            reachable = result.returncode == 0
            if reachable:
                logger.info(f"{self.host}: [pingDevice] Host is reachable (rc={result.returncode})")
            else:
                logger.warning(f"{self.host}: [pingDevice] Host did not respond (rc={result.returncode})")
            return reachable
        except Exception as e:
            logger.error(f"{self.host}: Ping failed with error: {e}")
            logger.info(f"{self.host}: Host is not reachable")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # reconnect_and_verify
    # ─────────────────────────────────────────────────────────────────────────
    def reconnect_and_verify(self, logger, interval = 120, max_retries=6, wait_time=30):

        #continuous ping instead of blind sleep
        if not self.pingDevice(logger, interval, wait_time):
            raise RuntimeError(f"{self.host}: Device never came back after reboot")

        # extra buffer for XR SSH
        logger.info(f"{self.host}: Waiting extra 120s for SSH readiness...")
        time.sleep(120)

        device_key = f"{self.host}_{self.vendor}_{self.model}"
        disconnect(device_key, logger)

        for attempt in range(max_retries):
            logger.info(f"{self.host}: Reconnect attempt {attempt + 1}/{max_retries}")

            conn = self.connect(logger)

            if conn:
                try:
                    output = conn.send_command("show version")

                    if output:
                        logger.info(f"{self.host}: SSH fully ready")
                        return conn, output

                except Exception as e:
                    logger.warning(f"{self.host}: Command failed — {e}")

            time.sleep(wait_time)

        raise RuntimeError(f"{self.host}: SSH not ready after retries")

    #----------------------------
    #Getting Active/Standby RSP
    #----------------------------
    def get_rsp_roles(self, conn, logger, device_key):
        try:

            rsp_json = None
            commands = device_results[device_key]["pre"]["execute_show_commands"]["commands"]

            for cmd in commands:
                if cmd.get("cmd") == "show redundancy":
                    rsp_json = cmd.get("json")
                    break

            if not rsp_json:
              logger.error("show redundancy output not found in device_results")
              return False

            ActiveNode  = rsp_json.get("ActiveNode")
            StandbyNode = rsp_json.get("StandbyNode")

            return ActiveNode , StandbyNode
        except Exception as e:
            msg = "Not able to logout from device for vendor: {self.vendor}"
            logger.error(msg)
            raise

    #---------------------
    # verify auto-fpd
    #---------------------
    def check_auto_fpd(self, conn, logger, models):
        """
        Auto FPD check & enable.
        """
        try:
            xr_fpd_enabled = False
            admin_fpd_enabled = False
            if self.vendor == "cisco":

                msg = f"{self.host}: Checking Auto FPD (Cisco XR)"
                logger.info(msg)
                commands = [
                    "fpd auto-upgrade enable",
                    "commit",
                    "exit"
                ]
                # ---------------- XR MODE ----------------
                xr_output = conn.send_command_timing("show running-config formal | include fpd", read_timeout=0, last_read=60)

                if "fpd auto-upgrade enable" in xr_output:
                    msg = f"{self.host}: Auto FPD already enabled in XR mode"
                    logger.info(msg)
                    xr_fpd_enabled = True
                else:
                    logger.warning(f"{self.host}: Enabling Auto FPD in XR mode")
                    conn.send_config_set(commands)
                    conn.exit_config_mode()
                    xr_fpd_enabled = True

                # ---------------- ADMIN MODE ----------------
                asr_models = next(d['asr9k'] for d in models if 'asr9k' in d)
                if self.model in asr_models:  # Club the admin and xr command. Create cmd lst on the go using the while
                    admin_output = conn.send_command_timing("admin show running-config | include fpd", read_timeout = 0, last_read = 60)

                    if "fpd auto-upgrade enable" in admin_output:
                        msg = f"{self.host}: Auto FPD already enabled in Admin mode"
                        logger.info(msg)
                        admin_fpd_enabled = True
                    else:
                        logger.warning(f"{self.host}: Enabling Auto FPD in Admin mode")
                        conn.send_config_set(commands)
                        conn.exit_config_mode()
                        admin_fpd_enabled = True

                result = {
                    "status": "ok",
                    "xr_fpd_enabled": xr_fpd_enabled,
                    "admin_fpd_enabled": admin_fpd_enabled,
                    "exception": "",
                    "verified": True
                }
                return result
                # Club Validae FPDs and Enable

        except Exception as e:
            result = {
                "status": "Failed",
                "xr_fpd_enabled": xr_fpd_enabled,
                "admin_fpd_enabled": admin_fpd_enabled,
                "exception": str(e),
                "verified": False
            }
            logger.exception(f"{self.host}: Auto FPD check failed")
            return result

    #-------------
    #Validate FPD
    #-------------

    def validateFPDs(self, conn, logger, device_key, post_reload=False):
        """
        Verify and upgrade Cisco FPDs using stored command output.
        Logic:
        - For Cisco, read 'show hw-module fpd' from device_results
        - Compare running vs programmed versions
        - Upgrade if versions differ
        """
        try:

            msg = "Starting Cisco FPD version verification..."
            logger.info(msg)

            #  Get stored output from device_results
            commands = device_results[device_key]["pre"]["execute_show_commands"]["commands"]
            fpd_output = None
            fpd_json = None


            for cmd in commands:

                if cmd.get("cmd") == "show hw-module fpd":
                    fpd_output = cmd.get("output")
                    fpd_json = cmd.get("json")
                    break

            if not fpd_output:
                logger.error("show hw-module fpd output not found in device_results")
                return {
                    "status":     "failed",
                    "exception":  "show hw-module fpd output not found in device_results"
                }

            # Parse output using existing parser
            fpd_list = fpd_json


            if not fpd_list:
                logger.warning("Parser returned no FPD data")
                return {
                    "status":     "failed",
                    "exception":  "Parser returned no FPD data"
                }

            # Extract FPD entries
            fpd_records = fpd_list.get("FPDs", [])

            if not fpd_records:
              logger.warning("No FPD entries parsed")
              return {
                  "status": "failed",
                  "exception": "No FPD entries parsed"
              }

            upgrade_required = []

            #  Compare versions

            for fpd in fpd_records:

                location = fpd.get("Location")
                fpd_name = fpd.get("FPDdevice")
                running = fpd.get("FPDVersions").get("Running")
                programmed = fpd.get("FPDVersions").get("Programd")
                atrStatus = fpd.get("ATRstatus")

                if not fpd:
                    logger.warning(f"Skipping invalid entry: {fpd}")
                    continue


                if (atrStatus != "CURRENT" and (running != programmed)):
                  upgrade_required.append(fpd)
                  msg = (f"Upgrade needed → {location} {fpd_name} \n"
                         f"(Running: {running}, Programmed: {programmed})")
                  logger.warning(msg)
                elif atrStatus == "N/A":
                    logger.info(f"Skipping {location} {fpd_name}: ATR status N/A")
                else:
                    logger.info(f"Up-to-date → {location} {fpd_name}")

            #  No upgrades needed
            if not upgrade_required:
                msg = "All FPDs are up-to-date"
                logger.info(msg)
                if post_reload:
                    logger.info("Cisco FPD upgrade procedure completed")
                    return {
                        "status": "ok",
                        "exception": "Cisco FPD upgrade procedure completed"
                    }
                return {"status": "ok", "exception": msg}
            logger.warning(f"{len(upgrade_required)} FPD(s) require upgrade")

            if post_reload:
                # If we’re already post-reload and still upgrades needed, stop here
                return {"status": "failed", "exception": "FPDs still require upgrade after reload"}


            #  Perform upgrades
            for fpd in upgrade_required:
                location = fpd.get("Location")
                fpd_name = fpd.get("FPDdevice")



                cmd = f"upgrade hw-module location {location} fpd {fpd_name}"
                logger.info(f"Executing: {cmd}")

                conn.send_command(cmd, expect_string=r"#")
                logger.info(f"Upgrade triggered for {location} {fpd_name}")
                interval = 120

                while True:
                    cmd = f"show  hw-module fpd | in {fpd_name}"
                    output = conn.send_command(cmd)
                    if "current" in output.lower():
                        logger.info(f"{fpd_name} Upgraded successfully")
                        break
                    time.sleep(interval)
                    interval += 120



            # ---- Reload device ----
            logger.info("Reloading device...")
            cmd = ["reload", "\n", "\n"]
            conn.send_multiline_timing(cmd, read_timeout=0, last_read=20)
#            conn.send_command("yes", expect_string=r"#", read_timeout=1200)

            # Reconnect
            conn, output = self.reconnect_and_verify(logger)
            if not output:
                msg = "Not able to connect to device"
                return {"status": "failed", "exception": msg}
            logger.info(f"{self.device_key} : Connected to device")

            # Self-call for post-reload validation
            return self.validateFPDs(conn, logger, device_key, post_reload=True)

        except Exception as e:
            logger.error(f"FPD verification/upgrade failed: {str(e)}")
            return {
                "status":     "failed",
                "exception":  str(e)
            }
    def checkStorageDualRE(self, conn, min_disk_gb, logger, cleanup=False):
        try:
            logger.info(f"[{self.device_key}] checkStorageDualRE — vendor: {self.vendor}")

            def _parse_junos_space(output, re_label):
                match = re.search(
                    r"^/dev/gpt/var\s+\S+\s+\S+\s+(\S+)",
                    output, re.M
                )
                if not match:
                    raise ValueError(
                        f"[{self.device_key}] checkStorageDualRE — "
                        f"could not parse /dev/gpt/junos for {re_label}"
                    )
                raw        = match.group(1).rstrip("%")
                size_match = re.match(r"^([\d.]+)\s*([GMTK]?)B?$", raw, re.IGNORECASE)
                if not size_match:
                    raise ValueError(
                        f"[{self.device_key}] checkStorageDualRE — "
                        f"unrecognised storage value '{raw}' for {re_label}"
                    )
                size_val   = float(size_match.group(1))
                size_unit  = size_match.group(2).upper()
                unit_to_gb = {"T": 1024, "G": 1, "M": 1 / 1024, "K": 1 / 1048576, "": 1}
                return size_val * unit_to_gb.get(size_unit, 1)

            logger.info(f"[{self.device_key}] checkStorageDualRE — querying RE0")
            re0_output = conn.send_command("show system storage", expect_string=r'.*>')
            re0_space  = _parse_junos_space(re0_output, "RE0")
            logger.info(f"[{self.device_key}] checkStorageDualRE — RE0 available: {re0_space:.2f} GB")

            logger.info(f"[{self.device_key}] checkStorageDualRE — querying RE1")
            re1_output = conn.send_command(
                "show system storage invoke-on other-routing-engine",
                expect_string=r'.*>'
            )
            re1_space = _parse_junos_space(re1_output, "RE1")
            logger.info(f"[{self.device_key}] checkStorageDualRE — RE1 available: {re1_space:.2f} GB")

            re0_low = re0_space < min_disk_gb
            re1_low = re1_space < min_disk_gb

            if cleanup:
                if re0_low:
                    logger.warning(
                        f"[{self.device_key}] checkStorageDualRE — RE0 low space "
                        f"({re0_space:.2f} GB < {min_disk_gb} GB), running cleanup"
                    )
                    conn.send_command(
                        "request system storage cleanup no-confirm",
                        expect_string=r'.*>',
                        read_timeout=300,
                    )
                    re0_output_post = conn.send_command("show system storage", expect_string=r'.*>')
                    re0_space       = _parse_junos_space(re0_output_post, "RE0 (post-cleanup)")
                    logger.info(
                        f"[{self.device_key}] checkStorageDualRE — RE0 after cleanup: {re0_space:.2f} GB"
                    )

                if re1_low:
                    logger.warning(
                        f"[{self.device_key}] checkStorageDualRE — RE1 low space "
                        f"({re1_space:.2f} GB < {min_disk_gb} GB), running cleanup"
                    )
                    conn.send_command(
                        "request system storage cleanup no-confirm invoke-on other-routing-engine",
                        expect_string=r'.*>',
                        read_timeout=300,
                    )
                    re1_output_post = conn.send_command(
                        "show system storage invoke-on other-routing-engine",
                        expect_string=r'.*>'
                    )
                    re1_space = _parse_junos_space(re1_output_post, "RE1 (post-cleanup)")
                    logger.info(
                        f"[{self.device_key}] checkStorageDualRE — RE1 after cleanup: {re1_space:.2f} GB"
                    )

                re0_ok = re0_space >= min_disk_gb
                re1_ok = re1_space >= min_disk_gb

                if not re0_ok or not re1_ok:
                    failed_res = []
                    if not re0_ok:
                        failed_res.append(f"RE0 {re0_space:.2f} GB")
                    if not re1_ok:
                        failed_res.append(f"RE1 {re1_space:.2f} GB")
                    msg = (
                        f"[{self.device_key}] checkStorageDualRE — insufficient space after cleanup: "
                        + ", ".join(failed_res)
                        + f" (min required: {min_disk_gb} GB)"
                    )
                    logger.error(msg)
                    return {
                        "status":     "failed",
                        "exception":  msg,
                        "sufficient": False,
                        "re0_space":  round(re0_space, 2),
                        "re1_space":  round(re1_space, 2),
                        "remark":     f"Still low after cleanup — RE0: {round(re0_space,2)}GB  RE1: {round(re1_space,2)}GB (min: {min_disk_gb}GB)",
                    }
            else:
                if re0_low and re1_low:
                    msg = "Not enough storage to transfer the image. Please do the device cleanup"
                    logger.error(f"[{self.device_key}] : {msg}")
                    return {
                        "status":     "failed",
                        "exception":  msg,
                        "sufficient": False,
                        "re0_space":  round(re0_space, 2),
                        "re1_space":  round(re1_space, 2),
                        "remark":     f"Insufficient — RE0: {round(re0_space,2)}GB  RE1: {round(re1_space,2)}GB (min: {min_disk_gb}GB)",
                    }

            result = {
                "status":     "ok",
                "exception":  "",
                "sufficient": True,
                "re0_space":  round(re0_space, 2),
                "re1_space":  round(re1_space, 2),
                "remark":     f"RE0: {round(re0_space,2)}GB  RE1: {round(re1_space,2)}GB — both above {min_disk_gb}GB threshold",
            }
            logger.info(f"[{self.device_key}] checkStorageDualRE — both REs OK: {result}")
            return result

        except Exception as e:
            msg = f"[{self.device_key}] checkStorageDualRE failed: {e}"
            logger.exception(msg)
            raise
    def checkStorage(self, conn, min_disk_gb, logger, cleanup):
        try:
            logger.info(f"[{self.vendor}_{self.model}] checkStorage — vendor: {self.vendor}")

            if self.vendor == "juniper":

                storage_output = conn.send_command("show system storage", expect_string=r'.*>')

                match = re.search(r"^/dev/gpt/var\s+\S+\s+\S+\s+(\S+)", storage_output, re.M)
                if not match:
                    raise ValueError(f"[{self.device_key}] Could not parse storage output")

                raw        = match.group(1).rstrip("%")
                size_match = re.match(r"^([\d.]+)\s*([GMTK]?)B?$", raw, re.IGNORECASE)
                if not size_match:
                    raise ValueError(f"[{self.device_key}] Unrecognised storage value: '{raw}'")
                size_val   = float(size_match.group(1))
                size_unit  = size_match.group(2).upper()
                unit_to_gb = {"T": 1024, "G": 1, "M": 1 / 1024, "K": 1 / 1048576, "": 1}
                avail_space = size_val * unit_to_gb.get(size_unit, 1)
                logger.info(f"[{self.device_key}] checkStorage — {avail_space:.2f} GB available")

            if self.vendor == "cisco":
                storage_output = conn.send_command_timing("show media", read_timeout = 0, last_read=30)
                match=re.search(r"harddisk:\s+\S+\s+\S+\s+\S+\s+(\S+)", storage_output, re.M).group(1)
                size_val   = match[:-1]
                size_unit  = match[-1:]
                unit_to_gb = {"T": 1024, "G": 1, "M": 1 / 1024, "K": 1 / 1048576, "": 1}
                avail_space = size_val * unit_to_gb.get(size_unit, 1)
                msg = f"[{self.vendor}_{self.model}] checkStorage — {avail_space} G available"
                logger.info(msg)

            # Enough space
            if float(avail_space) > min_disk_gb:
                result = {
                    "status":        "ok",
                    "deleted_files": [],
                    "exception":     "",
                    "sufficient":    True,
                }
                logger.info(f"[{self.vendor}_{self.model}] checkStorage — sufficient space: {result}")
                return result

            if cleanup:
                # ── LOW STORAGE → CLEANUP ─────────────────────────────────────────
                logger.warning(f"[{self.vendor}_{self.model}] checkStorage — low space, running cleanup")
                files_to_delete = self.device.get("cleanup_files", [])
                if not files_to_delete:
                    msg = f"[{self.vendor}_{self.model}] checkStorage — cleanup_files empty, cannot free space"
                    logger.error(msg)
                    return {
                        "status":        "failed",
                        "deleted_files": [],
                        "exception":     "cleanup_files empty",
                        "sufficient":    False,
                    }

                deleted_files = []
                for f in files_to_delete:
                    if self.vendor == "juniper":
                      cmd = [f"file delete {f}", "\n"]

                    if self.vendor == "cisco":
                      cmd = [
                        f"delete harddisk:/{f}",
                        "\n",
                      ]

                    logger.info(f"[{self.vendor}_{self.model}] checkStorage — deleting {f}")
                    conn.send_multiline_timing(cmd)
                    deleted_files.append(f)

                result = {
                    "status":        "low_space_cleaned",
                    "deleted_files": deleted_files,
                    "exception":     "",
                    "sufficient":    False,
                }

                if self.vendor == "cisco":
                  cmd = [
                        "install deactivate superseded",
                        "\n",
                        "install remove inactive all",
                        "\n",
                        "\n"
                  ]
                conn.send_multiline_timing(cmd)
                logger.info(f"[{self.vendor}_{self.model}] checkStorage — inactive packages deleted")
                result = {
                    "status":        "low_space_cleaned",
                    "deleted_files": deleted_files,
                    "inactive_packages": "deleted",
                    "exception":     "",
                    "sufficient":    False,
                }

                is_space = self.checkStorage(conn, min_disk_gb, logger, cleanup=False)
                if is_space.get("status") == "ok":
                    logger.info(f"[{self.device_key}] : Sufficient Space after cleanup ")
                    return result

                #storage recheck after deleting files
                if float(avail_space) <= min_disk_gb:
                  msg = f"[{self.vendor}_{self.model}] still low storage after cleanup"
                  logger.info(msg)
                  return False

                msg = f"[{self.vendor}_{self.model}] checkStorage — cleanup done: {result}"
                logger.info(msg)
                return result
            else:
                msg = f"[{self.vendor}_{self.model}] Not enough space in the device"
                logger.info(msg)
                return False

        except Exception as e:
            msg = f"[{self.vendor}_{self.model}] checkStorage failed: {e}"
            print(msg)
            logger.exception(msg)
            raise


    #----------------scp function----------
    def scpFile(self, conn, src, dest, logger):
        try:
            logger.info(f"[{self.device_key}] scpFile — {src} → {dest}")

            if self.vendor == "juniper":
                cmd = [
                    "start shell", "\n",
                    f"scp -C {src} {dest}", "yes","\n",
                    self.remote_password, "\n",
                    "exit", "\n",
                ]
            if self.vendor == "cisco":
                if self.model == "asr9910" or self.model == "asr9006": # model in the list.
                    cmd = [
                        f"scp {src} {dest} source-interface MgmtEth 0/RSP0/CPU0/0",
                        self.remote_password
                    ]
                if self.model == "ncs5501": # list in model and lowerc
                    cmd = [f"scp {src} {dest}", self.remote_password]
            output = conn.send_multiline_timing(cmd, read_timeout=0)
            if "No such file or directory" in output:
                logger.error(f"[{self.device_key}] scpFile — no such file: {src}")
                return False

            if not output:
                logger.error(f"[{self.device_key}] scpFile — no output returned")
                return False

            time.sleep(5)
            conn.clear_buffer()
            conn.find_prompt()

            logger.info(f"[{self.device_key}] scpFile — transfer complete")
            return True

        except Exception as e:
            logger.error(f"[{self.device_key}] scpFile failed: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    def preBackupDisk(self, conn, logger):
        try:
            logger.info(f"[{self.device_key}] preBackupDisk — vendor: {self.vendor}")

            if self.vendor not in self.accepted_vendors:
                raise ValueError(f"[{self.device_key}] preBackupDisk — unsupported vendor: {self.vendor}")

            if self.vendor == "juniper":
                output = conn.send_command("show vmhost version", read_timeout=300)

                if "set b" in output and "set p" in output:
                    logger.info(f"[{self.device_key}] preBackupDisk — dual disk, taking snapshot")
                    cmd    = "request vmhost snapshot"
                    output = conn.send_command_timing(cmd)
                    if cmd in output or "yes,no" in output.lower():
                        output += conn.send_command("yes", expect_string=r".*>", max_loops=3, read_timeout=900)
                    logger.info(f"[{self.device_key}] preBackupDisk — snapshot complete")
                    return {
                        "status":     "ok",
                        "exception":  "",
                        "disk_count": "dual",
                    }
                else:
                    logger.info(f"[{self.device_key}] preBackupDisk — single disk, skipping snapshot")
                    return {
                        "status":     "skipped",
                        "exception":  "",
                        "disk_count": "single",
                    }

        except Exception as e:
            msg = f"[{self.device_key}] preBackupDisk failed: {e}"
            logger.error(msg)
            return {
                "status":     "failed",
                "exception":  str(e),
                "disk_count": "",
            }

    # ─────────────────────────────────────────────────────────────────────────
    def preBackup(self, conn, filename, logger, device_key, models):
        try:
            logger.info(f"[{self.device_key}] preBackup — vendor: {self.vendor}")

            if self.vendor == "juniper":
                pre_backup_config = False
                pre_device_log    = False

                # Step 1: Backup running config
                config_commands = [f"save {filename}", "run file list"]
                config_backup   = conn.send_config_set(config_commands, cmd_verify=False, strip_command=True)
                if config_backup:
                    logger.info(f"[{self.device_key}] preBackup — config saved, SCP to remote server")
                    src      = f"/var/home/lab/{filename}"
                    dest     = f"{self.remote_server}:/var/tmp/{filename}"
                    if self.scpFile(conn, src, dest, logger):
                        pre_backup_config = True
                    else:
                        return {
                            "status":      "failed",
                            "exception":   "SCP of config file failed",
                            "config_file": filename,
                            "log_file":    "",
                            "destination": dest,
                        }

                # Step 2: Backup device log
                log_commands = [
                    f"request support information | save /var/log/{filename}.txt",
                    f"file archive compress source /var/log/* destination /var/tmp/{filename}.tgz",
                ]

                for cmd in log_commands:
                    logger.info(f"[{self.device_key}] preBackup — waiting for command to complete: {cmd}")
                    print(f"[preBackup] sending: {cmd}")

                    output = conn.send_command(
                        cmd,
                        expect_string=r".*>",   # wait until the device prompt returns
                        read_timeout=90000,        # give it up to 15 mins — archive can be slow
                        strip_prompt=True,
                        strip_command=True,
                    )
                logger.info(f"[{self.device_key}] preBackup — logs archived, SCP to remote server")
                src  = f"/var/tmp/{filename}.tgz"
                dest = f"{self.remote_server}:/var/tmp/{filename}.tgz"
                if self.scpFile(conn, src, dest, logger):
                    pre_device_log = True
                else:
                    return {
                        "status":      "failed",
                        "exception":   "SCP of log file failed",
                        "config_file": filename,
                        "log_file":    f"{filename}.tgz",
                        "destination": dest,
                    }

                if not pre_backup_config or not pre_device_log:
                    return {
                        "status":      "failed",
                        "exception":   "Config or log backup incomplete",
                        "config_file": filename,
                        "log_file":    f"{filename}.tgz",
                        "destination": self.remote_server,
                    }

                return {
                    "status":      "ok",
                    "exception":   "",
                    "config_file": filename,
                    "log_file":    f"{filename}.tgz",
                    "destination": self.remote_server,
                }

            if self.vendor == "cisco":
                asr_models = next(d['asr9k'] for d in models if 'asr9k' in d)
                ncs_models = next(d['ncs'] for d in models if 'ncs' in d)

                if self.model in ncs_models:
                    config_commands = [
                        f"copy running-config harddisk:{filename}-xr",
                        "\n"
                    ]

                if self.model in asr_models:
                    active_rsp, standby_rsp = self.get_rsp_roles(conn,logger, device_key)
                    logger.info(f"{device_key}: active RSP :{active_rsp}")
                    if not active_rsp:
                        logger.error(f"{self.host}: Active RSP not found")
                        return False
                    config_commands = [
                        f"copy running-config harddisk:{filename}-xr",
                        "\n",
                        f"admin copy running-config harddisk:{filename}-admin location {active_rsp}/VM1",
                        "\n"
                    ]
                backup_config = conn.send_multiline_timing(config_commands,cmd_verify = False)

                if not backup_config:
                    msg = f"{self.host}: Not able to save the file. Please look into to the preBakup()"
                    logger.info(msg)
                    return {
                        "status":      "failed",
                        "exception":   "Running Config backup incomplete",
                        "config_file": filename,
                        "log_file":    f"{filename}.cfg",
                        "destination": "/harddisk:",
                    }

                return {
                    "status":      "ok",
                    "exception":   "",
                    "config_file": filename,
                    "log_file":    f"{filename}",
                    "destination": "/harddisk:",
                }

        except Exception as e:
            msg = f"[{self.device_key}] preBackup failed: {e}"
            logger.error(msg)
            return {
                "status":      "failed",
                "exception":   str(e),
                "config_file": "",
                "log_file":    "",
                "destination": "",
            }


    # ─────────────────────────────────────────────────────────────────────────
    def transferImage(self, conn, image_path, target_image, logger, models):
        try:

            logger.info(f"[{self.device_key}] transferImage — {target_image}, vendor: {self.vendor}")
            src  = f"{self.remote_server}:{image_path}/{target_image}"

            if self.vendor == "juniper":
                dest = "/var/tmp/"
            if self.vendor == "cisco":
                asr_models = next(d['asr9k'] for d in models if 'asr9k' in d)
                ncs_models = next(d['ncs'] for d in models if 'ncs' in d)

                if self.model in asr_models:
                    dest = "/harddisk:"
                if self.model in ncs_models :
                    dest = "/misc/disk1/"

            if not self.scpFile(conn, src, dest, logger):
                return {
                    "status":      "failed",
                    "exception":   f"SCP transfer failed for {target_image}",
                    "image":       target_image,
                    "destination": dest,
                }

            logger.info(f"[{self.device_key}] transferImage — {target_image} transferred to {dest}")
            return {
                "status":      "ok",
                "exception":   "",
                "image":       target_image,
                "destination": dest,
            }

        except Exception as e:
            logger.error(f"[{self.device_key}] transferImage failed: {e}")
            return {
                "status":      "failed",
                "exception":   str(e),
                "image":       "",
                "destination": "",
            }

    #----change LPTS------------
    def changeLpts(self, conn, logger):
        """
        Vendor-based control plane protection change.
        Cisco XR:
        Modify LPTS (Local Packet Transport Services) policing
        Example: change SSH rate limit
        """
        try:
            msg = f"[{self.device_key}] : Modifying LPTS policer"
            logger.info(msg)
            print(msg)

            #  Clear leftover buffer after show commands
            conn.clear_buffer()

            #  Enter config mode manually (XR-safe)
            conn.send_command("configure terminal", expect_string=r"\(config\)#")

            #  Apply LPTS command safely on IOS-XR
            conn.send_command(
                "lpts pifib hardware police flow ssh known rate 50000",
                expect_string=r"\(config\)#"
            )

            #  Commit
            conn.send_command("commit", expect_string=r"#")

            #  Exit config mode
            conn.send_command("end", expect_string=r"#")

            msg = "LPTS modified successfully"
            logger.info(msg)
            return {
                "status": "ok",
                "exception": "",
                "lpts rate": 50000
            }

        except Exception as e:
            logger.exception(f"[{self.device_key}] : Control-plane protection change failed")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    #verify checksum
    # ─────────────────────────────────────────────────────────────────────────
    def verifyChecksum(self, conn, image, expected_checksum, logger):
        try:
            logger.info(f"[{self.device_key}] verifyChecksum — image: {image}, vendor: {self.vendor}")

            if self.vendor == "juniper":
                command = f"file checksum md5 /var/tmp/{image}"

                # Drain any leftover buffer before sending
                conn.send_command("\n", expect_string=r".*>", read_timeout=30)

                output = conn.send_command(
                    command,
                    expect_string=r".*>",
                    read_timeout=300
                )

                match = re.search(r"\.tgz\)\s*=\s*(\S+)", output)

            if self.vendor == "cisco":
                command = f"show md5 file /harddisk:/{image}"
                logger.info(f"[{self.device_key}]: Executing '{command}'")

                output = conn.send_command(
                    command,
                    expect_string=r"#",
                    read_timeout=120
                )

                match = re.search(r'([a-fA-F0-9]{32})',output)

            if not match:
                return {
                    "image":     image,
                    "status":    "failed",
                    "exception": f"Could not parse MD5 from output: {output[:200]}",
                    "expected":  expected_checksum,
                    "computed":  None,
                    "match":     False,
                }

            computed = match.group(1).strip()
            matched  = computed == expected_checksum.strip()

            logger.info(f"[{self.device_key}] verifyChecksum — match: OK")

            return {
                "image":     image,
                "status":    "ok" if matched else "failed",
                "exception": "" if matched else "Checksum mismatch",
                "expected":  expected_checksum,
                "computed":  computed,
                "match":     matched,
            }

        except Exception as e:
            logger.error(f"[{self.device_key}] verifyChecksum failed: {e}")
            return {
                "image":     image,
                "status":    "failed",
                "exception": str(e),
                "expected":  expected_checksum,
                "computed":  None,
                "match":     False,
            }

