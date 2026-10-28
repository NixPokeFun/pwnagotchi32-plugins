import logging
import threading
import subprocess
import time
import os
import shutil
import glob
import pwnagotchi
import pwnagotchi.plugins as plugins


class BcapUpdate(plugins.Plugin):
    __author__ = 'flippedgannet'
    __version__ = '0.3.3'
    __description__ = 'background bettercap OUI and caplets updater with pwnagotchi.cap protection, log cleaner, and recovery wipe in MANU mode'

    def __init__(self):
        self.running = False

    def on_loaded(self):
        logging.info("[update] Plugin loaded. Scheduling background update check...")
        thread = threading.Thread(target=self._delayed_start)
        thread.daemon = True
        thread.start()

    def _delayed_start(self):
        # Wait 30 seconds for interface stability
        time.sleep(30)

        try:
            cmd = subprocess.run(['pgrep', '-a', 'pwnagotchi'], stdout=subprocess.PIPE, text=True)
            process_info = cmd.stdout.lower()

            if '--manual' in process_info or ' -m' in process_info:
                self._run_update_task()
            else:
                logging.info("[update] Pwnagotchi is NOT in MANU mode (AUTO detected). Skipping background update.")
        except Exception as e:
            logging.error("[update] Error checking process mode: %s", e)

    def _clean_old_logs(self):
        logging.info("[update] Cleaning old Bettercap log files and recovery data...")

        recovery_file = '/root/.pwnagotchi-recovery'
        if os.path.exists(recovery_file):
            try:
                os.remove(recovery_file)
                logging.info("[update] Removed session recovery file %s", recovery_file)
            except Exception as e:
                logging.warning("[update] Could not remove recovery file %s: %s", recovery_file, e)
        else:
            logging.debug("[update] Recovery file not found, nothing to delete.")

        log_patterns = [
            '/var/log/bettercap.log*',
            '/root/bettercap-*.log'
        ]
        for pattern in log_patterns:
            for log_file in glob.glob(pattern):
                try:
                    if log_file.endswith('.gz') or log_file.endswith('.1') or os.path.getsize(log_file) > 10 * 1024 * 1024:
                        os.remove(log_file)
                        logging.info("[update] Removed old log file: %s", log_file)
                except Exception as e:
                    logging.warning("[update] Could not remove log file %s: %s", log_file, e)

    def _update_oui_database(self):
        """Force update OUI database with multiple fallback sources"""
        oui_file = '/usr/local/share/bettercap/oui.txt'
        oui_backup = '/usr/local/share/bettercap/oui.txt.bak'

        # Backup existing OUI
        if os.path.exists(oui_file):
            shutil.copy2(oui_file, oui_backup)
            logging.info("[update] Backed up existing OUI database")

        # Working OUI sources
        oui_sources = [
            'https://www.wireshark.org/download/automated/data/manuf',
            'https://standards-oui.ieee.org/oui/oui.txt'
        ]

        for source in oui_sources:
            try:
                logging.info(f"[update] Trying OUI source: {source}")
                oui_tmp = '/tmp/oui.txt.tmp'

                subprocess.run(
                    ['/usr/bin/wget', '-q', '-T', '20', '-t', '2', '-O', oui_tmp, source],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=60
                )

                if os.path.exists(oui_tmp) and os.path.getsize(oui_tmp) > 50000:
                    os.replace(oui_tmp, oui_file)
                    logging.info(f"[update] OUI database updated successfully from {source}")
                    if os.path.exists(oui_backup):
                        os.remove(oui_backup)
                    return True
                else:
                    if os.path.exists(oui_tmp):
                        os.remove(oui_tmp)
                    logging.warning(f"[update] OUI source {source} failed, trying next...")

            except Exception as e:
                logging.warning(f"[update] Error with {source}: {e}")
                continue

        # Restore backup if all sources failed
        if os.path.exists(oui_backup):
            shutil.copy2(oui_backup, oui_file)
            os.remove(oui_backup)
            logging.warning("[update] All OUI sources failed, restored backup")
        else:
            logging.warning("[update] All OUI sources failed and no backup available")

        return False

    def _run_update_task(self):
        if self.running:
            return
        self.running = True

        logging.info("[update] Starting background update task...")
        try:
            # Step 1: Clean old logs and recovery file
            self._clean_old_logs()

            # Step 2: Check internet connectivity
            logging.info("[update] Checking internet connectivity...")
            ping_res = subprocess.run(
                ['/bin/ping', '-c', '1', '-W', '3', '1.1.1.1'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            if ping_res.returncode != 0:
                logging.warning("[update] No internet connection detected. Aborting update.")
                return

            logging.info("[update] Internet connection verified.")

            # Step 3: Backup and update Bettercap caplets
            caplet_dir = '/usr/local/share/bettercap/caplets'
            pwn_caplet = os.path.join(caplet_dir, 'pwnagotchi.cap')
            pwn_bak = os.path.join(caplet_dir, 'pwnagotchi.cap.bak')

            if os.path.exists(pwn_caplet):
                shutil.copy2(pwn_caplet, pwn_bak)
                logging.info("[update] Backed up system pwnagotchi.cap")

            try:
                logging.info("[update] Updating Bettercap caplets...")
                bcap_cmd = ['/usr/bin/bettercap', '-eval', 'caplets.update; quit']
                bcap_res = subprocess.run(
                    bcap_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=60
                )

                if bcap_res.returncode == 0:
                    logging.info("[update] Bettercap caplets updated successfully.")
                else:
                    logging.error("[update] Bettercap caplets update failed:\n%s", bcap_res.stderr.strip())
            finally:
                # Guaranteed restoration of system pwnagotchi.cap even on runtime crashes
                if os.path.exists(pwn_bak):
                    shutil.copy2(pwn_bak, pwn_caplet)
                    os.remove(pwn_bak)
                    logging.info("[update] Restored original pwnagotchi.cap")

            # Step 4: Update OUI database
            self._update_oui_database()

        except Exception as e:
            logging.error("[update] Unexpected error during update task: %s", e)
        finally:
            self.running = False
