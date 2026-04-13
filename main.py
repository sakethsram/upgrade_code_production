# main.py
import logging
import sys
import threading
import os
from datetime import datetime
from typing import *
from concurrent.futures import ThreadPoolExecutor, as_completed

from lib.utilities import *
from prechecks import PreCheck
from upgrade import Upgrade
from postchecks import PostCheck

MAX_THREADS = 5

MX204_MODELS   = {"mx204"}
DUAL_RE_MODELS = {"mx240", "mx480"} # needs to be dynamic

# ─────────────────────────────────────────────────────────────────────────────
# execute_show_commands
# ─────────────────────────────────────────────────────────────────────────────
def execute_show_commands(device_key, vendor, model, conn, check_type, logger):
    commands         = load_commands(vendor, model, logger)
    if not commands:
        logger.error(f"[{device_key}] execute_show_commands — no commands loaded, aborting")
        return False

    entries = collect_outputs(device_key, vendor, commands, check_type, conn, logger)
    if not entries:
        logger.warning(f"[{device_key}] execute_show_commands — collect_outputs returned nothing")

    parse_outputs(device_key, vendor, check_type,model, logger)
    return True


def validate_device_dict(data: dict, device_key, logger):
    """
    Validate a device upgrade dictionary.
    Ensures required keys exist and values are of correct type.
    """

    required_keys = {
        "host": str,
        "vendor": str,
        "model": str,
        "device_type": str,
        "curr_image": str,
        "curr_os": str,
        "smu_upgrade": bool,
        "intermediate_release": bool,
        "image_storage": Union[int, float],
        "upgrade_storage": Union[int, float],
        "username": str,
        "password": str,
        "imageDetails": list,
        "image_path": str,
        "remote_backup_server": str,
        "remote_password": str,
        "cleanup_files": list,
    }

    errors = []

    # Validate required keys and types
    for key, expected_type in required_keys.items():
        if key not in data:
            errors.append(f"Missing required key: {key}")
            logger.error(f"[{device_key}] : Missing required key: {key}")
        else:
            if not isinstance(data[key], expected_type):
                errors.append(
                    f"Invalid type for {key}: expected {expected_type.__name__}, got {type(data[key]).__name__}"
                )
                logger.error(f"[{device_key}] : Invalid type for {key}: expected {expected_type.__name__}, got {type(data[key]).__name__}")

    if "smu_image_path" in data and data["smu_image_path"] is not None:
        if not isinstance(data["smu_image_path"], str):
            msg = f"Invalid type for smu_image_path: expected str, got {type(data['smu_image_path']).__name__}"
            errors.append(msg)
            logger.error(f"[{device_key}] : {msg}")


    # Validate imageDetails entries
    if "imageDetails" in data and isinstance(data["imageDetails"], list):
        for idx, entry in enumerate(data["imageDetails"], start=1):
            if not isinstance(entry, dict):
                msg = f"imageDetails[{idx}] must be a dict"
                errors.append(msg)
                logger.error(f"[{device_key}] : {msg}")
                continue
            if "expected_os" not in entry:
                msg = f"imageDetails[{idx}] missing 'expected_os'"
                errors.append(msg)
                logger.error(f"[{device_key}] : {msg}")

            if data.get("intermediate_release", False):
                if "intermediate_image" not in entry and idx == 1:
                    msg = f"imageDetails[{idx}] missing 'intermediate_image' for intermediate release"
                    errors.append(msg)
                    logger.error(f"[{device_key}] : {msg}")


            if data.get("smu_upgrade", False):
                if "smu_images" not in entry and idx == len(data["imageDetails"]):
                    msg = f"imageDetails[{idx}] missing 'smu_images' for SMU Upgrade"
                    errors.append(msg)
                    logger.error(f"[{device_key}] : {msg}")

            if "xr_committed_pkg" in entry and not isinstance(entry["xr_committed_pkg"], list):
                msg = f"imageDetails[{idx}].xr_committed_pkg must be a list"
                errors.append(msg)
                logger.error(f"[{device_key}] : {msg}")

            if "admin_committed_pkg" in entry and not isinstance(entry["admin_committed_pkg"], list):
                msg = f"imageDetails[{idx}].admin_committed_pkg must be a list"
                errors.append(msg)
                logger.error(f"[{device_key}] : {msg}")

    # Validate cleanup_files entries
    if "cleanup_files" in data and isinstance(data["cleanup_files"], list):
        for f in data["cleanup_files"]:
            if not isinstance(f, str):
                msg = f"cleanup_files entry must be string, got {type(f).__name__}"
                errors.append(nsg)
                logger.error(f"[{device_key}] : {msg}")
    if errors:
        return {"status": "failed", "exception": errors}

    return {"status": "ok", "exception": "Validated Input files"}

# ─────────────────────────────────────────────────────────────────────────────
# run_prechecks
# Phase 1
# ─────────────────────────────────────────────────────────────────────────────
def run_prechecks(conn, dev: dict, device_key: str, models: list, logger):
    tid         = threading.get_ident()
    vendor_lc   = dev["vendor"].lower()
    model_lc    = str(dev["model"]).lower().replace("-", "")
    host        = dev.get("host")
    image_storage = dev.get("image_storage")
    upgrade_storage = dev.get("upgrade_storage")

    logger.info(f"models: {models} and type: {type(models)}")

    logger.info(f"[THREAD-{tid}] [{device_key}] Prechecks started at {datetime.now()}")
    precheck = PreCheck(dev, device_key)
    try:
        # ──  Validating input file (pre) ───────────────────────────────
        logger.info(f"[{device_key}] : Validating the device input file")
        validate_input = validate_device_dict(dev, device_key, logger)
        if not validate_device_dict:
            msg = f"[{device_key}] : Not able to validate the device inputs"
            logger.error(msg)
            return False
        if validate_input.get("status") == "failed":
            raise RuntimeError(validate_input.get("exception", "Device input validity failed"))

        logger.info(f"[{device_key}] : {validate_input.get("exception")} ")

        # ──  Execute show commands (pre) ───────────────────────────────
        print(f"[{device_key}] Executing show commands")
        logger.info(f"[{device_key}] Executing show commands")

        exec_ok = execute_show_commands(device_key, vendor_lc, model_lc, conn, "pre", logger)
        if not exec_ok:
            msg = f"{host}: execute_show_commands() failed (collections/parsing)"
            logger.error(f"[{device_key}] EXECUTE failed — {msg}")
            device_results[device_key]["pre"]["execute_show_commands"]["exception"] = msg
            return False

        logger.info(f"[{device_key}] execute_show_commands OK")

#        # ──  Show version ──────────────────────────────────────────────
#        logger.info(f"[{device_key}] : Fetch the device details")
#        commands = device_results[device_key]["pre"]["execute_show_commands"]["commands"]
#        version_json = None
#
#        for cmd in commands:
#            if cmd.get("cmd") == "show version" or cmd.get("cmd") == "sh version" :
#                version_json = cmd.get("json")
#                break
#
#
#        if not version_json:
#          logger.error("show version output not found in device_results")
#          return False
#
#        if "hostname" in version_json:
#            device_results[device_key]["pre"]["show_version"] = {
#                "status":    "ok",
#                "exception": "",
#                "version":   version_json.get("version"),
#                "platform":  version_json.get("model"),
#                "hostname":  version_json.get("hostname")
#            }
#            device_results[device_key]["device_info"]["hostname"] = version_json.get("hostname")
#            device_results[device_key]["device_info"]["version"]  = version_json.get("version")
#            device_results[device_key]["device_info"]["model"] = version_json.get("model")
#        else:
#            device_results[device_key]["pre"]["show_version"] = {
#                "status":    "ok",
#                "exception": "",
#                "version":   version_json.get("version"),
#                "platform":  version_json.get("model"),
#                "hostname":  "",
#            }
#            device_results[device_key]["device_info"]["version"]  = version_json.get("version")
#            device_results[device_key]["device_info"]["model"] = version_json.get("model")
#
#
#        logger.info(
#            f"[{device_key}] [pre] show_version parsed — "
#            f'hostname={version_json.get("hostname")}  model={version_json.get("model")}  version={version_json.get("version")}'
#        )

        # ──  Show version ──────────────────────────────────────────────
        try:
            ok = get_show_version(device_key, conn, vendor_lc, logger, check_type="pre")
            if not ok:
                raise RuntimeError("get_show_version returned False")
        except Exception as e:
            logger.error(f"[{device_key}]  SHOW VERSION failed — {e}")
            device_results[device_key]["pre"]["show_version"]["exception"] = str(e)
            logger.warning(f"[{device_key}]  failed but continuing prechecks")


        # ── Backup active filesystem (disk1 → disk2) ─────────────────
        if vendor_lc == "juniper":
          try:
              if model_lc in DUAL_RE_MODELS:
                logger.info(f"[{device_key}] PRE — dual-RE model ({model_lc}): preBackupDiskDualRE()")
                backup_disk = precheck.preBackupDiskDualRE(conn, logger )
              else:
                logger.info(f"[{device_key}] STEP 4 — single-RE model ({model_lc}): preBackupDisk()")
                backup_disk = precheck.preBackupDisk(conn, logger)
              #remark_data 1
              device_results[device_key]["pre"]["backup_active_filesystem"] = backup_disk

              if backup_disk.get("status") == "failed":
                raise RuntimeError(backup_disk.get("exception", "Disk backup failed"))

          except Exception as e:
              logger.error(f"[{device_key}]  BACKUP DISK failed — {e}")
              device_results[device_key]["pre"]["backup_active_filesystem"]["exception"] = str(e)
              return False

          logger.info(f"[{device_key}]  backup disk OK")

        # ── Backup running config  ─────────────────────
        try:
            pre_check_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename            = f"{vendor_lc}_{model_lc}_{pre_check_timestamp}"
            backup              = precheck.preBackup(conn, filename, logger, device_key, models)
            #remark_2
            device_results[device_key]["pre"]["backup_running_config"] = backup

            if not backup:
                raise RuntimeError("preBackup returned False")
            if isinstance(backup, dict) and backup.get("status") == "failed":
                raise RuntimeError(backup.get("exception", "Config backup failed"))

        except Exception as e:
            logger.error(f"[{device_key}] BACKUP CONFIG failed — {e}")
            device_results[device_key]["pre"]["backup_running_config"]["exception"] = str(e)
            return False

        logger.info(f"[{device_key}] backup config OK")

        # ── Validate FPDs and Enable Auto FPDs ─────────────────────
        if vendor_lc == "cisco":
          validate_FPD  = precheck.validateFPDs(conn, logger, device_key)
          if not validate_FPD:
            msg = f"{host}: validateFPDs() failed"
            logger.error(f"[{device_key}] validateFPDs failed — {msg}")
            device_results[device_key]["pre"]["validateFPDs"]["exception"] = msg
            return False

          if isinstance(validate_FPD, dict) and validate_FPD.get("status") == "failed":
            raise RuntimeError(validate_FPD.get("exception", "Validate FPD failed"))

          check_auto_fpd = precheck.check_auto_fpd(conn,logger, models)
          if not check_auto_fpd:
            msg = f"{host}: check_auto_fpd() failed"
            logger.error(f" PRE - Auto_FPD_check failed — {msg}")
            device_results[device_key]["pre"]["check_auto_fpd"]["exception"] = msg
            return False

          if check_auto_fpd.get("status") == "failed":
              msg = f"{host}: check_auto_fpd() failed"
              logger.error(f" PRE - Auto_FPD_check failed — {msg}")
              device_results[device_key]["pre"]["check_auto_fpd"] = check_auto_fpd
              return False

          device_results[device_key]["pre"]["check_auto_fpd"] = check_auto_fpd
          logger.info(f"[{device_key}] Auto FPD enabled: {check_auto_fpd.get("status")}")


        # ── Merge pre results into device_results ─────────────────────
        try:
            thread_result = {
                "pre":         device_results.get(device_key, {}).get("pre", {}),
                "device_info": device_results.get(device_key, {}).get("device_info", {}),
                "upgrade":     device_results.get(device_key, {}).get("upgrade", {}),
            }
            merge_thread_result(device_key, thread_result)
        except Exception as e:
            logger.error(f"[{device_key}] MERGE failed — {e}")
            return False

        logger.info(f"[THREAD-{tid}] [{device_key}] All pre-checks passed")
        return True

    except Exception as e:
        logger.error(f"[THREAD-{tid}] [{device_key}] run_prechecks unhandled exception: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# run_upgrade
# ─────────────────────────────────────────────────────────────────────────────
def run_upgrade(conn, device: dict, device_key: str, accepted_vendors: list, logger, models):
    host          = device.get("host")
    vendor        = device.get("vendor").lower()
    model         = str(device.get("model")).lower().replace("-", "")
    image_details = device.get("imageDetails", [])
    curr_image    = device.get("curr_image")
    curr_os       = device.get("curr_os")
    smu_upgrade   = device.get("smu_upgrade")
    image_storage = device.get("image_storage")
    upgrade_storage = device.get("upgrade_storage")

    tid = threading.get_ident()
    logger.info(f"[THREAD-{tid}] [{device_key}] Upgrade started at {datetime.now()}")
    logger.info(
        f"[{device_key}] run_upgrade — host={host}, vendor={vendor}, model={model}, "
        f"curr_os={curr_os}, total_hops={len(image_details)}"
    )
    logger.info(f"[{device_key}] Running Upgrade...")


    # Seed rollback chain with the original image/OS from YAML
    rollback_image = [{"image": curr_image, "expected_os": curr_os}]
    logger.debug(f"[{device_key}] Rollback chain seeded — image={curr_image}, os={curr_os}")

    device_results[device_key]["upgrade"]["status"] = "in_progress"

    upgrade = Upgrade(device_key, device, accepted_vendors)

    image_path = device.get("image_path")
    precheck = PreCheck(device, device_key)

    try:

        for i, details in enumerate(image_details):

            if details.get("intermediate_image"):
                image = details.get("intermediate_image")
                expected_os = details.get("expected_os")
                checksum = details.get("checksum")
                xr_committed_pkg = details.get("xr_committed_pkg")
                admin_committed_pkg = details.get("admin_committed_pkg")
            elif details.get("smu_images"):
                continue
            else:
                image       = details.get("image")
                expected_os = details.get("expected_os")
                checksum    = details.get("checksum")
                xr_committed_pkg = details.get("xr_committed_pkg")
                admin_committed_pkg = details.get("admin_committed_pkg")

            logger.info(
                f"[{device_key}] ── Hop [{i}/{len(image_details)-1}] ── "
                f"image={image}, expected_os={expected_os}"
            )

            if not image or not expected_os or not checksum:
                msg = (
                    f"{host}: imageDetails[{i}] missing one of: "
                    f"image, expected_os, checksum"
                )
                logger.error(f"[{device_key}] {msg}")
                device_results[device_key]["upgrade"]["status"]    = "failed"
                device_results[device_key]["upgrade"]["exception"] = msg
                return conn, False

            logger.info(f"[{device_key}] Hop [{i}] — image={image}, expected_os={expected_os}")
            print(f"[{device_key}] Hop [{i}] upgrading with {image}")

            # ── CheckStorage for transfer image ─────────────────────

            if vendor == "juniper":
              if model in DUAL_RE_MODELS:
                  logger.info(f"[{device_key}] dual-RE model ({model}): checkStorageDualRE()")
                  storage = precheck.checkStorageDualRE(conn, image_storage, logger, cleanup = False)
              else:
                  logger.info(f"[{device_key}] single-RE model ({model}): checkStorage()")

            storage  = precheck.checkStorage(conn, image_storage, logger, cleanup = False)
            if not storage:
                msg = f"{host}: checkStorage() failed for image transfer. Please clean up the device to transfer image into device for upgrade."
                logger.error(f"[{device_key}] STORAGE failed for transfering image — {msg}")
                device_results[device_key]["pre"]["check_storage"]["exception"] = msg
                return False
            #remark_3
            device_results[device_key]["pre"]["check_storage"] = storage
            logger.info(f"[{device_key}] storage OK")

            # ── Change LPTS rate for file transfer ─────────────────────
            if vendor == "cisco":
                lpts_rate = precheck.changeLpts(conn, logger)
                if not lpts_rate:
                    msg = f"changeLpts() failed"
                    logger.error(f"[{device_key}] Not able to change the LPTS rate - {msg}")
                    device_results[device_key]["pre"]["change_lpts_rate"]["exception"] = msg
                    return False
                device_results[device_key]["pre"]["change_lpts_rate"] = lpts_rate
                logger.info(f"[{device_key}] Change LPTS Rate OK")

            # ── Transfering image and Verify MD5 checksum for every image in imageDetails ───────
            try:
                try:
                    transfer = precheck.transferImage(conn, image_path, image, logger, models)
                    device_results[device_key]["pre"]["transfer_image"].append({
                      "status":    transfer.get("status"),
                      "exception": transfer.get("exception", ""),
                      "image":  transfer.get("image", ""),
                      "destination": transfer.get("destination", "")
                    })
                    if transfer.get("status") == "failed":
                        raise RuntimeError(transfer.get("exception", "Image transfer failed"))
                except Exception as e:
                    logger.error(f"[{device_key}] TRANSFER IMAGE failed — {e}")
                    device_results[device_key]["pre"]["transfer_image"].append({
                      "status":    "failed",
                      "exception": str(e),
                      "image":  image,
                      "destination": ""
                    })
                    return False

                logger.info(f"[{device_key}]  transfer image OK")
                checksum_result = precheck.verifyChecksum(conn, image, checksum, logger)

                print(f" checksum_result   = {checksum_result}")

                device_results[device_key]["pre"]["verify_checksum"].append({
                    "image":     checksum_result.get("image"),
                    "status":    checksum_result.get("status"),
                    "exception": checksum_result.get("exception", ""),
                    "expected":  checksum_result.get("expected", ""),
                    "computed":  checksum_result.get("computed", ""),
                    "match":     checksum_result.get("match", False),
                })

                if not checksum_result.get("match"):
                    print(f" FAILED for image [{i}]: {image}")
                    logger.error(f"[{device_key}]  VERIFY CHECKSUM failed — {image}")
                    return False

                print(f" image [{i}] checksum OK — {image}")
                logger.info(f"[{device_key}]  [{i}] checksum OK — {image}")

            except Exception as e:
                logger.error(f"[{device_key}] exception for image [{i}] {image} — {e}")
                print(f" EXCEPTION image [{i}]: {e}")
                device_results[device_key]["pre"]["verify_checksum"].append({
                    "image":     image,
                    "status":    "failed",
                    "exception": str(e),
                    "expected":  checksum,
                    "computed":  "",
                    "match":     False,
                })
                return False

            # ── CheckStorage for Device ─────────────────────
            if vendor == "juniper":
              if model in DUAL_RE_MODELS:
                  logger.info(f"[{device_key}] dual-RE model ({model}): checkStorageDualRE()")
                  storage = precheck.checkStorageDualRE(conn, image_storage, logger, cleanup = True)
              else:
                  logger.info(f"[{device_key}] single-RE model ({model}): checkStorage()")

            storage  = precheck.checkStorage(conn, upgrade_storage, logger, cleanup = True)
            if not storage:
                msg = f"{host}: checkStorage() failed for Upgrade"
                logger.error(f"[{device_key}] STORAGE failed — {msg}")
                device_results[device_key]["pre"]["check_storage"]["exception"] = msg
                return False

            device_results[device_key]["pre"]["check_storage"] = storage
            logger.info(f"[{device_key}] storage OK")


            if vendor =="cisco" :
              asr_models = next(d['asr9k'] for d in models if 'asr9k' in d)
              ncs_models = next(d['ncs'] for d in models if 'ncs' in d)
              if model in asr_models:
                prompt = conn.find_prompt()
                hostname = prompt.replace("#","").strip()
                msg = f"Hostname->{hostname}"
                logger.info(msg)
                if "OSA" in hostname or "TYO" in hostname:
                  apply_deny_any=upgrade.apply_deny_policy(conn,logger)
                  if not apply_deny_any:
                    msg = "Failed to apply_deny_any policy to neighbors"
                    logger.info(msg)
                    return False

                msg="Hostname does not contain OSA or TYO"
                logger.info(msg)

              #Set overload bit
              set_overload_bit=upgrade.set_overload_bit(conn,logger, models)
              if not set_overload_bit:
                msg = "Failed to set overload bit"
                logger.error(f"[{device_key} set_overload_bit fialed - {msg}]")
                device_results[device_key]["upgrade"]["set_overload_bit"]["exception"] = msg
                return False

              device_results[device_key]["upgrade"]["set_overload_bit"]= set_overload_bit
              logger.info(f"[{device_key}]  Overload bit Set OK")

              if not xr_committed_pkg or not admin_committed_pkg: # validate in prechecks.
                msg = f"No committed packages provided. Please provide the packages to validate the upgrade"
                logger.error(f"[{device_key}]: committed packages are not provided")
                return False
              logger.info(f"[{device_key}]  Committed packages are provide for both XR and admin")

              logger.info(f"[{device_key}] Starting Image Upgrade ")
              conn, is_upgrade = upgrade.imageUpgrade(conn, expected_os, image,i, logger, models, xr_committed_pkg, admin_committed_pkg)

            if vendor == "juniper":
                if model in DUAL_RE_MODELS:
                    logger.info(f"[{device_key}] using dual-RE upgrade path")
                    conn, is_upgrade = upgrade.run_upgrade_dualRE(conn,image_details, curr_os, curr_image, logger)
                else:
                    logger.info(f"[{device_key}] Starting Image Upgrade ")
                    conn, is_upgrade = upgrade.imageUpgrade(conn, expected_os, image, i, logger, models )

            if not is_upgrade:
                msg = f"Upgrade hop [{i}] failed for {image}"
                logger.error(f"[{device_key}] {msg}")
                device_results[device_key]["upgrade"]["status"]    = "failed"
                device_results[device_key]["upgrade"]["exception"] = msg

                logger.info(f"[{device_key}] Triggering rollback...")
                logger.debug(
                    f"[{device_key}] Rollback chain at failure: "
                    + str([e.get("image") for e in rollback_image])
                )
                print(f"[{device_key}] Upgrade failed — starting rollback") # input set for rollback with current device state, timestmap, image, version.
                return conn, False

            # Hop succeeded — add to rollback chain so we can unwind to here if needed
            rollback_image.append({"image": image, "expected_os": expected_os})
            logger.info(f"[{device_key}] Hop [{i}] succeeded — rollback chain now {len(rollback_image)} entries")

        msg = f"All {len(image_details)} upgrade hop(s) successful"
        logger.info(f"[{device_key}] {msg}")
        print(f"[{device_key}] {msg}")
        device_results[device_key]["upgrade"]["status"]    = "success"
        device_results[device_key]["upgrade"]["exception"] = ""
        return conn, True

    except Exception as e:
        msg = f"run_upgrade unhandled exception: {e}"
        logger.error(f"[{device_key}] {msg}")
        device_results[device_key]["upgrade"]["status"]    = "failed"
        device_results[device_key]["upgrade"]["exception"] = str(e)
        return conn, False

# ─────────────────────────────────────────────────────────────────────────────
# run_smu_upgrade
# ─────────────────────────────────────────────────────────────────────────────
def run_smu_upgrade(conn, device: dict, device_key: str, accepted_vendors: list, logger, models):
    host          = device.get("host")
    vendor        = device.get("vendor")
    model         = str(device.get("model")).lower().replace("-", "")
    image_details = device.get("imageDetails", [])
    smu_upgrade   = device.get("smu_upgrade")
    curr_image    = device.get("curr_image")
    curr_os       = device.get("curr_os")

    tid = threading.get_ident()
    logger.info(f"[THREAD-{tid}] [{device_key}] Upgrade started at {datetime.now()}")
    logger.info(
        f"[{device_key}] run_upgrade — host={host}, vendor={vendor}, model={model}, "
        f"curr_os={curr_os}, total_hops={len(image_details)}"
    )
    logger.info(f"[{device_key}] Running SMU Upgrade...")


    device_results[device_key]["upgrade"]["status"] = "in_progress"

    upgrade = Upgrade(device_key, device, accepted_vendors)

    image_path = device.get("smu_image_path")
    precheck = PreCheck(device, device_key)

    try:
        smu_list = image_details[-1].get("smu_images", [])
        xr_committed_pkg = image_details[-1].get("xr_committed_pkg", [])
        admin_committed_pkg = image_details[-1].get("admin_committed_pkg", [])

        for j,smu in enumerate(smu_list):
            image = smu["image"]
            checksum = smu["checksum"]

            if not image or not checksum:
                msg = (
                    f"{host}: imageDetails[{j+1}] missing one of: "
                    f"image, checksum"
                )
                logger.error(f"[{device_key}] {msg}")
                device_results[device_key]["upgrade"]["status"]    = "failed"
                device_results[device_key]["upgrade"]["exception"] = msg
                return conn, False

            logger.info(f"[{device_key}] Hop [{j+1}] — image={image}")

            try:
                try:
                    transfer = precheck.transferImage(conn, image_path, image, logger, models)
                    device_results[device_key]["pre"]["transfer_image"].append({
                      "status":    transfer.get("status"),
                      "exception": transfer.get("exception", ""),
                      "image":  transfer.get("image", ""),
                      "destination": transfer.get("destination", "")
                    })
                    if transfer.get("status") == "failed":
                        raise RuntimeError(transfer.get("exception", "Image transfer failed"))
                except Exception as e:
                    logger.error(f"[{device_key}] TRANSFER IMAGE failed — {e}")
                    device_results[device_key]["pre"]["transfer_image"][j]["exception"] = str(e)
                    return False

                logger.info(f"[{device_key}]  transfer image OK")
                checksum_result = precheck.verifyChecksum(conn, image, checksum, logger)


                device_results[device_key]["pre"]["verify_checksum"].append({
                    "image":     checksum_result.get("image"),
                    "status":    checksum_result.get("status"),
                    "exception": checksum_result.get("exception", ""),
                    "expected":  checksum_result.get("expected", ""),
                    "computed":  checksum_result.get("computed", ""),
                    "match":     checksum_result.get("match", False),
                })

                if not checksum_result.get("match"):
                    logger.error(f"[{device_key}]  VERIFY CHECKSUM failed — {image}")
                    return False

                logger.info(f"[{device_key}]  [{j+1}] checksum OK — {image}")

            except Exception as e:
                logger.error(f"[{device_key}] exception for image [{j+1}] {image} — {e}")
                device_results[device_key]["pre"]["verify_checksum"][j]["exception"] = str(e)
                return False

        smu_file = " /".join([smu.get("image", "") for smu in smu_list if smu.get("image")])
        logger.info(f"[{device_key}] Final SMU file string: {smu_file}")

        conn, is_smu_upgrade = upgrade.upgrade_smu(conn, smu_file,xr_committed_pkg, admin_committed_pkg, len(image_details)-1, logger, models)
        logger.debug(f"[{device_key}] : SMU Upgrade returned is_smu_upgrade={is_smu_upgrade}")

        if not is_smu_upgrade:
            msg = f"SMU Upgrade failed for {image}"
            logger.error(f"[{device_key}] {msg}")
            device_results[device_key]["upgrade"]["status"]    = "failed"
            device_results[device_key]["upgrade"]["exception"] = msg

            return conn, False

        msg = f"All {len(image_details)} upgrade hop(s) successful"
        logger.info(f"[{device_key}] {msg}")
        device_results[device_key]["upgrade"]["status"]    = "success"
        device_results[device_key]["upgrade"]["exception"] = ""
        return conn, True


    except Exception as e:
        msg = f"run_smu_upgrade unhandled exception: {e}"
        logger.error(f"[{device_key}] {msg}")
        device_results[device_key]["upgrade"]["status"]    = "failed"
        device_results[device_key]["upgrade"]["exception"] = str(e)
        return conn, False

# ─────────────────────────────────────────────────────────────────────────────
# run_rollback
# ─────────────────────────────────────────────────────────────────────────────
def run_rollback(conn, device: dict, device_key: str, accepted_vendors: list, logger):
    host        = device.get("host")
    original_os = device.get("curr_os")
    vendor        = device.get("vendor").lower()
    model         = str(device.get("model")).lower().replace("-", "")
    image_details = device.get("imageDetails", [])
    curr_image    = device.get("curr_image")
    curr_os       = device.get("curr_os")
    smu_upgrade   = device.get("smu_upgrade")
    image_storage = device.get("image_storage")
    upgrade_storage = device.get("upgrade_storage")

    tid = threading.get_ident()
    logger.info(f"[THREAD-{tid}] [{device_key}] Upgrade started at {datetime.now()}")
    logger.info(
        f"[{device_key}] run_upgrade — host={host}, vendor={vendor}, model={model}, "
        f"curr_os={curr_os}, total_hops={len(image_details)}"
    )
    logger.info(f"[{device_key}] Running Upgrade...")




    device_results[device_key]["upgrade"]["status"] = "in_progress"

    upgrade = Upgrade(device_key, device, accepted_vendors)

    image_path = device.get("image_path")
    precheck = PreCheck(device, device_key)

    logger.info(f"[{device_key}] Rollback started at {datetime.now()}")
    logger.info(
        f"[{device_key}] run_rollback — host={host}, vendor={vendor}, "
        f"curr_os={curr_os}")
    logger.inffo(f"[{device_key}] Running Rollback...")

    upgrade = Upgrade(device_key, device, accepted_vendors)

    try:

        for i, details in enumerate(image_details):

            if details.get("intermediate_image"):
                image = details.get("intermediate_image")
                expected_os = details.get("expected_os")
                checksum = details.get("checksum")
                xr_committed_pkg = details.get("xr_committed_pkg")
                admin_committed_pkg = details.get("admin_committed_pkg")
            elif details.get("smu_images"):
                continue
            else:
                image       = details.get("image")
                expected_os = details.get("expected_os")
                checksum    = details.get("checksum")
                xr_committed_pkg = details.get("xr_committed_pkg")
                admin_committed_pkg = details.get("admin_committed_pkg")

            logger.info(
                f"[{device_key}] ── Hop [{i}/{len(image_details)-1}] ── "
                f"image={image}, expected_os={expected_os}"
            )

            if not image or not expected_os or not checksum:
                msg = (
                    f"{host}: imageDetails[{i}] missing one of: "
                    f"image, expected_os, checksum"
                )
                logger.error(f"[{device_key}] {msg}")
                device_results[device_key]["upgrade"]["status"]    = "failed"
                device_results[device_key]["upgrade"]["exception"] = msg
                return conn, False

            logger.info(f"[{device_key}] Hop [{i}] — image={image}, expected_os={expected_os}")
            print(f"[{device_key}] Hop [{i}] upgrading with {image}")

            # ── CheckStorage for transfer image ─────────────────────

            if vendor == "juniper":
              if model in DUAL_RE_MODELS:
                  logger.info(f"[{device_key}] dual-RE model ({model}): checkStorageDualRE()")
                  storage = precheck.checkStorageDualRE(conn, image_storage, logger, cleanup = False)
              else:
                  logger.info(f"[{device_key}] single-RE model ({model}): checkStorage()")

            storage  = precheck.checkStorage(conn, image_storage, logger, cleanup = False)
            if not storage:
                msg = f"{host}: checkStorage() failed for image transfer. Please clean up the device to transfer image into device for upgrade."
                logger.error(f"[{device_key}] STORAGE failed for transfering image — {msg}")
                device_results[device_key]["pre"]["check_storage"]["exception"] = msg
                return False
            device_results[device_key]["pre"]["check_storage"] = storage
            logger.info(f"[{device_key}] storage OK")

            # ── Change LPTS rate for file transfer ─────────────────────
            if vendor == "cisco":
                lpts_rate = precheck.changeLpts(conn, logger)
                if not lpts_rate:
                    msg = f"changeLpts() failed"
                    logger.error(f"[{device_key}] Not able to change the LPTS rate - {msg}")
                    device_results[device_key]["pre"]["change_lpts_rate"]["exception"] = msg
                    return False
                device_results[device_key]["pre"]["change_lpts_rate"] = lpts_rate
                logger.info(f"[{device_key}] Change LPTS Rate OK")

            # ── Transfering image and Verify MD5 checksum for every image in imageDetails ───────
            try:
                try:
                    transfer = precheck.transferImage(conn, image_path, image, logger, models)
                    device_results[device_key]["pre"]["transfer_image"].append({
                      "status":    transfer.get("status"),
                      "exception": transfer.get("exception", ""),
                      "image":  transfer.get("image", ""),
                      "destination": transfer.get("destination", "")
                    })
                    if transfer.get("status") == "failed":
                        raise RuntimeError(transfer.get("exception", "Image transfer failed"))
                except Exception as e:
                    logger.error(f"[{device_key}] TRANSFER IMAGE failed — {e}")
                    device_results[device_key]["pre"]["transfer_image"].append({
                      "status":    "failed",
                      "exception": str(e),
                      "image":  image,
                      "destination": ""
                    })
                    return False

                logger.info(f"[{device_key}]  transfer image OK")
                checksum_result = precheck.verifyChecksum(conn, image, checksum, logger)

                print(f" checksum_result   = {checksum_result}")

                device_results[device_key]["pre"]["verify_checksum"].append({
                    "image":     checksum_result.get("image"),
                    "status":    checksum_result.get("status"),
                    "exception": checksum_result.get("exception", ""),
                    "expected":  checksum_result.get("expected", ""),
                    "computed":  checksum_result.get("computed", ""),
                    "match":     checksum_result.get("match", False),
                })

                if not checksum_result.get("match"):
                    print(f" FAILED for image [{i}]: {image}")
                    logger.error(f"[{device_key}]  VERIFY CHECKSUM failed — {image}")
                    return False

                print(f" image [{i}] checksum OK — {image}")
                logger.info(f"[{device_key}]  [{i}] checksum OK — {image}")

            except Exception as e:
                logger.error(f"[{device_key}] exception for image [{i}] {image} — {e}")
                print(f" EXCEPTION image [{i}]: {e}")
                device_results[device_key]["pre"]["verify_checksum"].append({
                    "image":     image,
                    "status":    "failed",
                    "exception": str(e),
                    "expected":  checksum,
                    "computed":  "",
                    "match":     False,
                })
                return False

            # ── CheckStorage for Device ─────────────────────
            if vendor == "juniper":
              if model in DUAL_RE_MODELS:
                  logger.info(f"[{device_key}] dual-RE model ({model}): checkStorageDualRE()")
                  storage = precheck.checkStorageDualRE(conn, image_storage, logger, cleanup = True)
              else:
                  logger.info(f"[{device_key}] single-RE model ({model}): checkStorage()")

            storage  = precheck.checkStorage(conn, upgrade_storage, logger, cleanup = True)
            if not storage:
                msg = f"{host}: checkStorage() failed for Upgrade"
                logger.error(f"[{device_key}] STORAGE failed — {msg}")
                device_results[device_key]["pre"]["check_storage"]["exception"] = msg
                return False

            device_results[device_key]["pre"]["check_storage"] = storage
            logger.info(f"[{device_key}] storage OK")


            if vendor =="cisco" :
              asr_models = next(d['asr9k'] for d in models if 'asr9k' in d)
              ncs_models = next(d['ncs'] for d in models if 'ncs' in d)
              if model in asr_models:
                prompt = conn.find_prompt()
                hostname = prompt.replace("#","").strip()
                msg = f"Hostname->{hostname}"
                logger.info(msg)
                print(msg)
                if "OSA" in hostname or "TYO" in hostname:
                  apply_deny_any=upgrade.apply_deny_policy(conn,logger)
                  if not apply_deny_any:
                    msg = "Failed to apply_deny_any policy to neighbors"
                    logger.info(msg)
                    print(msg)
                    return False

                msg="Hostname does not contain OSA or TYO"
                logger.info(msg)
                print(msg)

              #Set overload bit
              set_overload_bit=upgrade.set_overload_bit(conn,logger, models)
              if not set_overload_bit:
                msg = "Failed to set overload bit"
                logger.error(f"[{device_key} set_overload_bit fialed - {msg}]")
                device_results[device_key]["upgrade"]["set_overload_bit"]["exception"] = msg
                return False

              device_results[device_key]["upgrade"]["set_overload_bit"]= set_overload_bit
              logger.info(f"[{device_key}]  Overload bit Set OK")

              if not xr_committed_pkg or not admin_committed_pkg: # validate in prechecks.
                msg = f"No committed packages provided. Please provide the packages to validate the upgrade"
                logger.error(f"[{device_key}]: committed packages are not provided")
                return False
              logger.info(f"[{device_key}]  Committed packages are provide for both XR and admin")

              logger.info(f"[{device_key}] Starting Image Upgrade ")
              conn, is_upgrade = upgrade.imageUpgrade(conn, expected_os, image,i, logger, models, xr_committed_pkg, admin_committed_pkg)

            if vendor == "juniper":
                if model in DUAL_RE_MODELS:
                    logger.info(f"[{device_key}] using dual-RE upgrade path")
                    conn, is_upgrade = upgrade.run_upgrade_dualRE(conn,image_details, curr_os, curr_image, logger)
                else:
                    logger.info(f"[{device_key}] Starting Image Upgrade ")
                    conn, is_upgrade = upgrade.imageUpgrade(conn, expected_os, image, i, logger, models )

            if not is_upgrade:
                msg = f"Upgrade hop [{i}] failed for {image}"
                logger.error(f"[{device_key}] {msg}")
                device_results[device_key]["upgrade"]["status"]    = "failed"
                device_results[device_key]["upgrade"]["exception"] = msg
                return conn, False



            # Hop succeeded — add to rollback chain so we can unwind to here if needed
            logger.info(f"[{device_key}] Hop [{i}] succeeded")

        msg = f"All {len(image_details)} upgrade hop(s) successful"
        logger.info(f"[{device_key}] {msg}")
        print(f"[{device_key}] {msg}")
        device_results[device_key]["upgrade"]["status"]    = "success"
        device_results[device_key]["upgrade"]["exception"] = ""
        return conn, True

    except Exception as e:
        msg = f"run_upgrade unhandled exception: {e}"
        logger.error(f"[{device_key}] {msg}")
        device_results[device_key]["upgrade"]["status"]    = "failed"
        device_results[device_key]["upgrade"]["exception"] = str(e)
        return conn, False

# ─────────────────────────────────────────────────────────────────────────────
# run_postchecks
# Phase 3 — same thread, conn handed over from run_upgrade.
#
# Uses the EXACT same utility calls as run_prechecks.
# The only difference from pre is check_type="post" — results land in
#   device_results[key]["post"][...] instead of ["pre"][...]
#
# Steps:
#   1. show version         — non-fatal (same rule as pre STEP 2)
#   2. execute show commands — fatal    (same rule as pre STEP 1)
#   3. enable_re_protect_filter — stub slot, set aside for future
# ─────────────────────────────────────────────────────────────────────────────
def run_postchecks(conn, dev: dict, device_key: str, logger, models):
    tid       = threading.get_ident()
    vendor_lc = dev["vendor"].lower()
    model_lc  = str(dev["model"]).lower().replace("-", "")
    host      = dev.get("host")

    logger.info(f"[THREAD-{tid}] [{device_key}] Postchecks started at {datetime.now()}")
    postcheck = PostCheck(dev, device_key)
    precheck = PreCheck(dev, device_key)

    try:
        # ── STEP 1: Show version (post) ───────────────────────────────────────
        # Same call as pre STEP 2 — only check_type differs.
        # Non-fatal: log error, write exception, continue to STEP 2.
        logger.info(f"[{device_key}] POST STEP 1: show version")

        try:
            ok = get_show_version(device_key, conn, vendor_lc, logger, check_type="post")
            if not ok:
                raise RuntimeError("get_show_version returned False")
            logger.info(
                f"[{device_key}] POST STEP 1 show_version OK — "
                f"version={device_results[device_key]['post']['show_version'].get('version', '?')}"
            )
        except Exception as e:
            logger.error(f"[{device_key}] POST STEP 1 SHOW VERSION failed — {e}")
            device_results[device_key]["post"]["show_version"]["exception"] = str(e)
            logger.warning(f"[{device_key}] POST STEP 1 failed but continuing postchecks")



        if vendor_lc == "cisco":
            #---------- Clear configuration inconsistency --------------------------------#
            try:

                logger.info(f"[{device_key}] : Clearing the configuration inconsistency")
                cmd = "clear configuration inconsistency"
                output = conn.send_command(cmd)
                if not output:
                  msg = "Not able to clear the configuration inconsistency"
                  logger.error(f"[{device_key}] : {msg}")
                  device_results[device_key]["post"]["config_inconsistency"] = {"status": "failed", "exception": msg,  "inconsistency": "" }
                  return False

                logger.info(f"[{device_key}]:: Config inconsistency cleared")
                device_results[device_key]["post"]["config_inconsistency"] = {"status": "ok", "exception": "",  "inconsistency": "cleared" }

            except Exception as e:
                logger.error(f"[{device_key}]:: Failed to clear config inconsistency: {e}")
                device_results[device_key]["post"]["config_inconsistency"] = {"status": "failed", "exception": str(e),  "inconsistency": "" }
                return False

            logger.info(f"[{device_key}] POST  validate configurion inconsistency OK — ")


            #---------- Validate FPDs are up-to-date --------------------------------#
            validate_FPD  = precheck.validateFPDs(conn, logger, device_key)
            if not validate_FPD:
              msg = f"{host}: validateFPDs() failed"
              logger.error(f"[{device_key}] validateFPDs failed — {msg}")
              device_results[device_key]["post"]["validateFPDs"]["exception"] = msg
              return False

            if validate_FPD.get("status") == "failed":
              msg = f"{validate_FPD.get('exception')} "
              logger.error(f"[{device_key}] validateFPDs failed — {msg}")
              device_results[device_key]["post"]["validateFPDs"] = validate_FPD
              return False

            device_results[device_key]["post"]["validateFPDs"] = validate_FPD
            logger.info(f"[{device_key}] Auto FPD enabled: OK")

            #---------- remove Overloadbit and deny-any policy --------------------------------#
            asr_models = next(d['asr9k'] for d in models if 'asr9k' in d)
            if model_lc in asr_models:
              prompt = conn.find_prompt()
              hostname = prompt.replace("#","").strip()
              msg = f"Hostname->{hostname}"
              logger.info(msg)
              print(msg)
              if "OSA" in hostname or "TYO" in hostname:
                remove_deny_any_policy=postcheck.remove_deny_any_policy(conn,logger)
                if not remove_deny_any_policy:
                  msg = "Failed to remove_deny_any_policy policy to neighbors"
                  logger.info(F"[{device_key}] : {msg}")
                  return False
              else:
                msg="Hostname does not contain OSA or TYO"
                logger.info(F"[{device_key}] : {msg}")

            #remove Set overload bit
            remove_overload_bit=postcheck.remove_overload_bit(conn,logger, models)
            if not remove_overload_bit:
              msg = "Failed to remove set overload bit"
              logger.error(f"[{device_key} remove_overload_bit fialed - {msg}]")
              device_results[device_key]["pre"]["remove_overload_bit"]["exception"] = msg
              return False
            device_results[device_key]["pre"]["remove_overload_bit"] = remove_overload_bit
            logger.info(f"[{device_key}]  remove Overload bit Set OK")

            #---------- Remove inactive packages --------------------------------#
            inactive_packages = postcheck.inactivePackage(conn, logger)
            if not inactive_packages:
              msg = f"[{device_key}] : inactive_packages() failed"
              logger.error(f"Remove Inactive Package failed - {msg}")
              device_results[device_key]["post"]["inactive_pkg"]["exception"] = msg
              return False
            device_results[device_key]["post"]["inactive_pkg"] = inactive_packages
            logger.info(f"[{device_key}] Remove Inactive Packages: OK")


        # ── STEP 2: Execute show commands (post) ──────────────────────────────
        # Same call as pre STEP 1 — only check_type="post" differs.
        # Fatal: Phase 4 diff needs post command outputs to exist.
        print(f"[{device_key}] POST : executing show commands")
        logger.info(f"[{device_key}] POST : executing show commands")
        exec_ok = execute_show_commands(device_key, vendor_lc, model_lc, conn, "post", logger)
        if not exec_ok:
            msg = f"[{device_key}]: execute_show_commands() failed during postchecks"
            logger.error(f"[{device_key}] POST-CHECK failed — {msg}")
            device_results[device_key]["post"]["execute_show_commands"]["exception"] = msg
            return False

        logger.info(f"[{device_key}] POST : execute_show_commands OK")


        try:
            ok = get_show_version(device_key, conn, vendor_lc, logger, check_type="post")
            if not ok:
                raise RuntimeError("get_show_version returned False")

        except Exception as e:
            logger.error(f"[{device_key}] POST STEP 1 SHOW VERSION failed — {e}")
            device_results[device_key]["post"]["show_version"]["exception"] = str(e)
            logger.warning(f"[{device_key}] POST STEP 1 failed but continuing postchecks")


#        # ──  Show version ──────────────────────────────────────────────
#        commands = device_results[device_key]["post"]["execute_show_commands"]["commands"]
#        version_json = None
#
#        for cmd in commands:
#            if cmd.get("cmd") == "show version" or cmd.get("cmd") == "sh version" :
#                version_json = cmd.get("json")
#                break
#
#
#        if not version_json:
#          logger.error("show version output not found in device_results")
#          return False
#
#        if "hostname" in version_json:
#            device_results[device_key]["post"]["show_version"] = {
#                "status":    "ok",
#                "exception": "",
#                "version":   version_json.get("version"),
#                "platform":  version_json.get("model"),
#                "hostname":  version_json.get("hostname")
#            }
#            device_results[device_key]["device_info"]["hostname"] = version_json.get("hostname")
#            device_results[device_key]["device_info"]["version"]  = version_json.get("version")
#        else:
#            device_results[device_key]["post"]["show_version"] = {
#                "status":    "ok",
#                "exception": "",
#                "version":   version_json.get("version"),
#                "platform":  version_json.get("model"),
#                "hostname":  "",
#            }
#            device_results[device_key]["device_info"]["version"]  = version_json.get("version")
#
#        logger.info(
#                f"[{device_key}] POST : show_version OK — "
#                f"version={device_results[device_key]['post']['show_version'].get('version', '?')}"
#            )

        logger.info(f"[{device_key}] POST Check: show version")

        try:
            ok = get_show_version(device_key, conn, vendor_lc, logger, check_type="post")
            if not ok:
                raise RuntimeError("get_show_version returned False")
            logger.info(
                f"[{device_key}] POST check - show_version OK — "
                f"version={device_results[device_key]['post']['show_version'].get('version', '?')}"
            )
        except Exception as e:
            logger.error(f"[{device_key}] POST CHECK- SHOW VERSION failed — {e}")
            device_results[device_key]["post"]["show_version"]["exception"] = str(e)
            logger.warning(f"[{device_key}] POST CHECK- failed but continuing postchecks")

                # ---- Post Upgrade snapshort for dualRE  ----- #
        if vendor_lc == "juniper":
            if model_lc in DUAL_RE_MODELS:
                logger.info(f"[{device_key}] : Taking Snapshot...")
                try:
                    snap_result = precheck.preBackupDiskDualRE(conn, logger)

                    device_results[device_key]["post"]["backup_active_filesystem"] = {
                        "status":        snap_result.get("status"),
                        "exception":     snap_result.get("exception", ""),
                        "snapshot_name": snap_result.get("snapshot_name", ""),
                        "creation_date": snap_result.get("creation_date", ""),
                        "junos_version": snap_result.get("junos_version", ""),
                        "verified":      snap_result.get("verified", False),
                    }

                    if snap_result.get("status") == "failed":
                        raise RuntimeError(
                          snap_result.get("exception", "Post-upgrade snapshot failed")
                        )

                        logger.info(
                          f"[{device_key}] POST DEVICE snapshot OK — "
                          f"snap={snap_result.get('snapshot_name')}  "
                          f"junos={snap_result.get('junos_version')}"
                        )
                except Exception as e:
                    logger.error(f"[{device_key}] POST DEVICE SNAPSHOT failed — {e}")
                    device_results[device_key]["post"]["backup_active_filesystem"]["exception"] = str(e)
                    return False
            else:
                logger.info(
                  f"[{device_key}] POST DEVICE Snapshot  — skipped "
                  f"(model={model_lc} is not dual-RE)"
                )

        if vendor_lc == "cisco":
            lpts_rate = postcheck.revertLpts(conn, logger) # after fpds.
            if not lpts_rate:
                msg = f"revertLpts() failed"
                logger.error(f"[{device_key}] Not able to revert the LPTS rate - {msg}")
                device_results[device_key]["post"]["revert_lpts_rate"]["exception"] = msg
                return False
            device_results[device_key]["post"]["revert_lpts_rate"] = lpts_rate
            logger.info(f"[{device_key}] Revert LPTS Rate Policy OK")

        # ── STEP 3: Enable RE protect filter — stub, set aside for future ─────
        # Slot already in device_results["post"]["enable_re_protect_filter"]
        # as {"status": "", "exception": ""} from init_device_results.
        # Nothing written here until implemented.
        logger.info(f"[{device_key}] POST STEP 3: enable_re_protect_filter stub — skipping")

        logger.info(f"[THREAD-{tid}] [{device_key}] All post-checks complete")
        return True

    except Exception as e:
        logger.error(f"[THREAD-{tid}] [{device_key}] run_postchecks unhandled exception: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# run_device_pipeline
#
# Phases are STRICTLY sequential on one thread.
# Each phase must fully return before the next one starts.
#
#   Phase 1 returns True   →  Phase 2 starts
#   Phase 2 returns True   →  Phase 3 starts
#   Phase 3 returns        →  Phase 4 starts
#   Phase 4 returns        →  finally{} runs
# ─────────────────────────────────────────────────────────────────────────────
def run_device_pipeline(dev: dict, accepted_vendors: list, models: list):
    vendor     = dev.get("vendor").lower()
    model      = str(dev.get("model")).lower().replace("-", "")
    host       = dev.get("host")
    smu_upgrade = dev.get("smu_upgrade")
    ip_clean   = host.replace(".", "_")
    device_key = f"{ip_clean}_{vendor}_{model}"

    dev["accepted_vendors"] = accepted_vendors

    init_device_results(device_key, host, vendor, model, dev)
    logger = setup_logger(device_key, vendor=vendor, model=model, host=host)

    tid = threading.get_ident()
    logger.info(f"[THREAD-{tid}] [{device_key}] Pipeline started at {datetime.now()}")
    logger.info(f"[{device_key}] ===== PIPELINE STARTED =====")

    conn = None

    try:
        # ── VENDOR CHECK ──────────────────────────────────────────────────────
        if vendor not in accepted_vendors:
            msg = (
                f"[{device_key}] Unsupported vendor '{vendor}' — "
                f"not in accepted_vendors {accepted_vendors}"
            )
            logger.error(msg)
            device_results[device_key]["pre"]["connect"]["exception"] = msg
            raise ConnectionError(msg)

        # ── CONNECT ───────────────────────────────────────────────────────────
        conn = connect(device_key, dev, logger)
        if not conn:
            msg = f"[{device_key}] connect() returned None"
            logger.error(msg)
            device_results[device_key]["pre"]["connect"]["exception"] = msg
            raise ConnectionError(msg)

        logger.info(f"[{device_key}] Connected to {host}")

        # ──--- PRE-CHECKS ───────────────────────────────────────────────
        logger.info(f"[{device_key}] ── PRE-CHECKS starting...")

        precheck_ok = run_prechecks(conn, dev, device_key, models, logger)
        if not precheck_ok:
            msg = f"[{device_key}] PRE-CHECKS FAILED — skipping upgrade"
            logger.error(msg)
            return False


        logger.info(f"[{device_key}] ── Pre-Checks COMPLETE — starting UPGRADE ...")

        # ──--- UPGRADE ──────────────────────────────────────────────────
        conn, upgrade_ok = run_upgrade(conn, dev, device_key, accepted_vendors, logger, models)
        device_results[device_key]["conn"] = conn

        if not upgrade_ok:
            msg = f"[{device_key}] UPGRADE FAILED — stopping device"
            logger.error(msg)
            return False

        # ──--- SMU UPGRADE ──────────────────────────────────────────────────
        if vendor == "cisco" and smu_upgrade:
            conn, smu_upgrade = run_smu_upgrade(conn, dev, device_key, accepted_vendors, logger, models)
            device_results[device_key]["conn"] = conn

            if not smu_upgrade:
              msg = f"[{device_key}]: SMU Upgrade Failed - Stopping device"
              logger.error(msg)
              return False
            logger.info(f"[{device_key}] ── SMU Upgrade Completed")


        logger.info(f"[{device_key}] ── Upgrade COMPLETE — starting PostCheck")

        # ──--- ROLLBACK ──────────────────────────────────────────────────
#        conn, rollback_ok = run_rollback(conn, dev, device_key, accepted_vendors, logger, models)
#        logger.info(f"[{device_key}] run_rollback completed — rollback_ok={rollback_ok}")
#
#        if not rollback_ok:
#            msg = f"Rollback also failed for {device_key} — stopping device"
#            logger.error(f"[{device_key}] {msg}")
#            device_results[device_key]["upgrade"]["exception"] = (
#                device_results[device_key]["upgrade"]["exception"]
#                + " | ROLLBACK FAILED"
#            )

        # ──--------POST-CHECKS ──────────────────────────────────────────────
        postcheck_ok = run_postchecks(conn, dev, device_key, logger, models)
        if not postcheck_ok:
            logger.warning(f"[{device_key}] POST-CHECK completed with errors — run_postcheck() failed")
        else:
            logger.info(f"[{device_key}] ── POST-CHECK COMPLETE")

        # Phase 3 fully returned — Phase 4 now starts.
        # pre.execute_show_commands and post.execute_show_commands are both
        # fully written into device_results at this point.

        # ── PHASE 4: DIFF ─────────────────────────────────────────────────────
        logger.info(f"[{device_key}] ── Comparison between PreCheck and PostCheck show commands starting ...")

        try:
            from diff import diff_devices
            diff_input  = {device_key: device_results.get(device_key, {})}
            diff_result = diff_devices(data=diff_input)
            device_results[device_key]["diff"] = diff_result.get(device_key, {})
            changed = len(device_results[device_key]["diff"])
            logger.info(f"[{device_key}] ── Comparison COMPLETE — {changed} command(s) with changes")

        except Exception as e:
            logger.error(f"[{device_key}] Comparison failed — {e}")
            device_results[device_key]["diff"] = {}

        # Phase 4 fully returned — finally{} now runs
        return True

    finally:
        try:
            export_device_summary(device_key)
            logger.info(f"[{device_key}] HTML report exported")
        except Exception as e:
            logger.error(f"[{device_key}] export_device_summary failed: {e}")

        disconnect(device_key, logger)
        logger.info(f"[THREAD-{tid}] [{device_key}] Pipeline finished at {datetime.now()}")
        logger.info(f"[{device_key}] ===== PIPELINE FINISHED =====")


# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    devices          = load_yaml("deviceDetails.yaml")
    all_devs         = devices["devices"]
    accepted_vendors = devices.get("accepted_vendors")
    models           = devices.get("models")
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {
            executor.submit(run_device_pipeline, dev, accepted_vendors, models): dev
            for dev in all_devs
        }
        for future in as_completed(futures):
            dev = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[MAIN] Thread error for {dev.get('host')}: {e}")

    sys.exit(0)


if __name__ == "__main__":
    main()
