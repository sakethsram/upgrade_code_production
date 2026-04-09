# postchecks.py
from lib.utilities import *


# ─────────────────────────────────────────────────────────────────────────────
# PostCheck class
# ─────────────────────────────────────────────────────────────────────────────
class PostCheck:
    """
    Handles post-upgrade checks.
    Mirrors the PreCheck interface — conn and logger are always passed in
    from run_postchecks() after the upgrade phase completes.

    Current steps (called from run_postchecks in main.py):
        1. show version  → get_show_version(..., check_type="post")
        2. show commands → execute_show_commands(..., check_type="post")

    Add vendor-specific post-check methods here as needed, following the same
    pattern as PreCheck (e.g. verifyRoutes, checkAlarms, compareProtocols).
    """

    def __init__(self, device: dict, device_key):
        self.device           = device
        self.host             = device.get("host")
        self.device_type      = device.get("device_type")
        self.vendor           = device.get("vendor")
        self.model            = device.get("model")
        self.username         = device.get("username")
        self.accepted_vendors = device.get("accepted_vendors", [])
        self.device_key       = device_key
    
    def clear_config_inconsistency(self, conn, logger):
        try:
            # Check the configuration inconsistency 
            try: 
              cmd = "sh configuration failed startup" # No need to check the config inconistency. 
              inconsistency = conn.send_command(cmd)
              
              if not inconsistency: 
                msg = "Not able to check the inconsistence configuraion . Please check the command"
                logger.error(f"[{self.device_key}] : {msg}")
                return {
                  "status": "failed", 
                  "exception": msg, 
                  "inconsistency": ""
                }
              
              if "!!" in inconsistency: 
                msg = "No Configuration inconsistency is there."
                logger.info(f"[{self.device_key}] : {msg}")
                return {
                  "status": "ok", 
                  "exception": "", 
                  "inconsistency": msg
                }
              logger.info(f"[{self.device_key}] : Configuration inconsistency is there. ")
              
            except Exception as e: 
              msg = "Checking configuration inconsistency failed"
              logger.exception(f"[{self.device_key}] : Checking configuration inconsistency failed")
              raise
            
            # Clearing configuration inconsistency
            logger.info(f"[{self.device_key}] : Clearing the configuration inconsistency") # run this command in main.py file of run_postchecks. 
            cmd = "clear configuration inconsistency"
            output = conn.send_command(cmd)
            if not output: 
              msg = "Not able to clear the configuration inconsistency" 
              logger.error(f"[{self.device_key}] : {msg}")
              return {
                "status": "failed", 
                "exception": msg, 
                "inconsistency": ""
              }
            logger.info(f"[{self.device_key}]:: Config inconsistency cleared")
            return {
              "status": "ok", 
              "exception": "", 
              "inconsistency": "cleared"
            }
        except Exception as e:
            logger.error(f"[{self.device_key}]:: Failed to clear config inconsistency: {e}")
            raise
    
    def inactivePackage(self, conn, logger): 
        try: 
            cmd = [
              "install deactivate superseded",
              "\n",
              "install remove inactive all",
              "\n",
              "\n"
            ]
            output = conn.send_multiline_timing(cmd)
            if not output: 
                msg = "Failed to delete the inactive packages"
                logger.error(f"[{self.device_key}] : {msg}")
                return {
                  "status": "failed", 
                  "inactive_packages": "not deleted", 
                  "exception": ""
                }
                
            logger.info(f"[{self.device_key}]  — inactive packages deleted")
            return {
              "status": "ok",
              "inactive_packages": "deleted",
              "exception": ""
            }
        except Exception as e: 
            logger.exception(f"[{self.device_key}] : incactive packages failed")
            raise
    
    #----Revert LPTS------------
    def revertLpts(self, conn, logger):
        """
        Vendor-based control plane protection change.
        Cisco XR:
        Modify LPTS (Local Packet Transport Services) policing
        Example: change SSH rate limit
        """
        try:
            
            msg = f"[{self.device_key}]: Revert LPTS Rate policy"
            logger.info(msg)
            commands = [
                "no lpts pifib hardware police",
                "commit",
                "exit"
            ]

            output = conn.send_config_set(commands, cmd_verify=False) + "\n"
            
            if not output: 
                msg = f"[{self.device_key}]: Not able to change the lpts rate "
                logger.info(msg)
                return {
                    "status": "failed",
                    "exception": msg
                }
                
            msg="LPTS reverted successfully"
            logger.info(msg)
            return {
                "status": "ok",
                "exception": ""
            }

        except Exception as e:
            logger.exception(f"[{self.device_key}]: Failed to revert the LPTS rate")
            raise
