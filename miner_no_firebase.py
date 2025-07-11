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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("miner.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

WALLET = os.getenv("MINER_WALLET", "mbc1q4xd0fvvj53jwwqaljz9kvrwqxxh0wqs5k89a05.Genzo")
POOL = os.getenv("MINER_POOL", "stratum+tcp://161.35.76.150:123")
ALGO = "power2b"
URL = "https://github.com/rplant8/cpuminer-opt-rplant/releases/download/5.0.27/cpuminer-opt-linux.tar.gz"
FILENAME = "cpuminer-opt-linux.tar.gz"
EXTRACTED_BIN = "cpuminer-sse2"
RENAMED_BIN = "miner"
THREADS = os.getenv("MINER_THREADS", str(multiprocessing.cpu_count() - 1))
EXPECTED_SHA256 = "46c16a4470e8c1dc22d574b90934c0d01db9dcdbce0b3cfd494aa70ec9631763"

def check_dependencies():
    logger.info("Checking dependencies...")
    for cmd in ["wget", "tar", "chmod"]:
        if shutil.which(cmd) is None:
            logger.error(f"Command '{cmd}' not found. Please install it.")
            sys.exit(1)

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

def download_miner():
    if os.path.exists(FILENAME):
        logger.info("File already exists, skipping download.")
        verify_checksum(FILENAME)
        return
    logger.info("Downloading miner...")
    try:
        urllib.request.urlretrieve(URL, FILENAME)
        verify_checksum(FILENAME)
        logger.info("Miner downloaded successfully")
    except Exception as e:
        logger.error(f"Failed to download miner: {e}")
        sys.exit(1)

def extract_miner():
    logger.info("Extracting miner...")
    try:
        with tarfile.open(FILENAME, "r:gz") as tar:
            tar.extractall()
        if os.path.exists(EXTRACTED_BIN):
            os.rename(EXTRACTED_BIN, RENAMED_BIN)
            os.chmod(RENAMED_BIN, 0o755)
            logger.info("Miner extracted and ready")
        else:
            logger.error("Extracted binary not found!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to extract miner: {e}")
        sys.exit(1)

def run_miner_with_restart():
    global miner_process
    while True:
        logger.info(f"Starting miner at {datetime.datetime.now()}")
        logger.info(f"Using {THREADS} threads")

        cmd = [f"./{RENAMED_BIN}", "-a", ALGO, "-o", POOL, "-u", WALLET, "-t", THREADS]
        try:
            miner_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = miner_process.communicate()
            if miner_process.returncode != 0:
                logger.error(f"Miner stopped with error: {stderr}")
            else:
                logger.info("Miner stopped normally")
        except Exception as e:
            logger.error(f"Error running miner: {e}")

        logger.info("Restarting miner in 10 seconds...")
        time.sleep(10)

def handle_shutdown(signum, frame):
    logger.info("Received shutdown signal, stopping miner...")
    if 'miner_process' in globals():
        miner_process.terminate()
        try:
            miner_process.wait(timeout=5)
            logger.info("Miner stopped gracefully")
        except subprocess.TimeoutExpired:
            miner_process.kill()
            logger.warning("Miner forcefully killed")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        check_dependencies()
        download_miner()
        extract_miner()
        run_miner_with_restart()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
