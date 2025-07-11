#!/usr/bin/env python3

import subprocess
import os
import shutil
import tarfile
import urllib.request
import multiprocessing
import datetime
import logging
import sys
import signal
import time
import hashlib

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("miner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Konfigurasi variabel miner
WALLET = os.getenv("MINER_WALLET", "mbc1q4xd0fvvj53jwwqaljz9kvrwqxxh0wqs5k89a05.Genzo")
POOL = os.getenv("MINER_POOL", "stratum+tcp://161.35.76.150:123")
ALGO = "power2b"
URL = "https://github.com/rplant8/cpuminer-opt-rplant/releases/download/5.0.27/cpuminer-opt-linux.tar.gz"
FILENAME = "cpuminer-opt-linux.tar.gz"
EXTRACTED_BIN = "cpuminer-sse2"
RENAMED_BIN = "miner"
THREADS = os.getenv("MINER_THREADS", str(multiprocessing.cpu_count() - 1))
EXPECTED_SHA256 = "21a7fdee90c3e6c3e4455c8ab76e765e038894ccdf9f7589a7e6825b8dbfcf8e"

# Cek dependensi dasar
def check_dependencies():
    logger.info("Checking required commands...")
    for cmd in ["tar", "chmod"]:
        if shutil.which(cmd) is None:
            logger.error(f"Missing command: {cmd}. Please install it or use alternate environment.")
            sys.exit(1)

# Verifikasi SHA256 file
def verify_checksum(file_path):
    logger.info("Verifying file checksum...")
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    if sha256_hash.hexdigest() != EXPECTED_SHA256:
        logger.error("Checksum verification failed!")
        sys.exit(1)
    logger.info("Checksum verified successfully.")

# Unduh binary miner
def download_miner():
    if os.path.exists(FILENAME):
        logger.info("Miner archive already exists, verifying...")
        verify_checksum(FILENAME)
        return
    logger.info("Downloading miner archive...")
    try:
        urllib.request.urlretrieve(URL, FILENAME)
        verify_checksum(FILENAME)
        logger.info("Download complete and verified")
    except Exception as e:
        logger.error(f"Failed to download: {e}")
        sys.exit(1)

# Ekstrak dan rename binary
def extract_miner():
    logger.info("Extracting miner...")
    try:
        with tarfile.open(FILENAME, "r:gz") as tar:
            tar.extractall()
        if os.path.exists(EXTRACTED_BIN):
            os.rename(EXTRACTED_BIN, RENAMED_BIN)
            os.chmod(RENAMED_BIN, 0o755)
            logger.info("Miner ready: renamed and permission set")
        else:
            logger.error("Miner binary not found after extraction.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        sys.exit(1)

# Jalankan miner dengan auto-restart
def run_miner_with_restart():
    global miner_process
    while True:
        logger.info(f"Launching miner at {datetime.datetime.now()} with {THREADS} threads")
        cmd = [f"./{RENAMED_BIN}", "-a", ALGO, "-o", POOL, "-u", WALLET, "-t", THREADS]
        try:
            miner_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = miner_process.communicate()
            if miner_process.returncode != 0:
                logger.error(f"Miner error: {stderr.strip()}")
            else:
                logger.info("Miner exited normally")
        except Exception as e:
            logger.error(f"Miner failed to start: {e}")

        logger.info("Restarting in 10 seconds...")
        time.sleep(10)

# Tangani shutdown / Ctrl+C
def handle_shutdown(signum, frame):
    logger.info("Shutdown signal received. Cleaning up...")
    if 'miner_process' in globals():
        miner_process.terminate()
        try:
            miner_process.wait(timeout=5)
            logger.info("Miner exited cleanly")
        except subprocess.TimeoutExpired:
            miner_process.kill()
            logger.warning("Force killed miner")
    sys.exit(0)

# Entry point utama
if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        check_dependencies()
        download_miner()
        extract_miner()
        run_miner_with_restart()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
