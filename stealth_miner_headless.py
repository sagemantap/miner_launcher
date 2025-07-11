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
import firebase_admin
from firebase_admin import credentials, db, messaging

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("miner.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Konfigurasi penambangan
WALLET = os.getenv("MINER_WALLET", "mbc1q4xd0fvvj53jwwqaljz9kvrwqxxh0wqs5k89a05.Yono")
POOL = os.getenv("MINER_POOL", "stratum+tcp://161.35.76.150:123")
ALGO = "power2b"
URL = "https://github.com/rplant8/cpuminer-opt-rplant/releases/download/5.0.27/cpuminer-opt-linux.tar.gz"
FILENAME = "cpuminer-opt-linux.tar.gz"
EXTRACTED_BIN = "cpuminer-sse2"
RENAMED_BIN = "miner"
THREADS = os.getenv("MINER_THREADS", str(multiprocessing.cpu_count() - 1))
EXPECTED_SHA256 = "your_expected_sha256_here"  # Ganti dengan checksum aktual

# Inisialisasi Firebase
def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("path/to/your/firebase-adminsdk.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://your-project-id.firebaseio.com'
        })
    logger.info("Firebase initialized")

# Log status ke Firebase Realtime Database
def log_to_firebase(status, details):
    ref = db.reference('mining_status')
    ref.push({
        'timestamp': datetime.datetime.now().isoformat(),
        'status': status,
        'details': details,
        'threads': THREADS,
        'wallet': WALLET,
        'pool': POOL
    })
    logger.info(f"Logged to Firebase: {status}")

# Kirim notifikasi FCM
def send_fcm_notification(title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        topic="mining_updates"
    )
    try:
        messaging.send(message)
        logger.info("FCM notification sent")
    except Exception as e:
        logger.error(f"Failed to send FCM notification: {e}")

# Periksa dependensi
def check_dependencies():
    logger.info("Checking dependencies...")
    for cmd in ["wget", "tar", "chmod"]:
        if shutil.which(cmd) is None:
            logger.error(f"Command '{cmd}' not found. Please install it.")
            sys.exit(1)

# Verifikasi checksum file
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

# Unduh miner
def download_miner():
    if os.path.exists(FILENAME):
        logger.info("File already exists, skipping download.")
        verify_checksum(FILENAME)
        return
    logger.info("Downloading miner...")
    try:
        urllib.request.urlretrieve(URL, FILENAME)
        verify_checksum(FILENAME)
        log_to_firebase("download", "Miner downloaded successfully")
    except Exception as e:
        logger.error(f"Failed to download miner: {e}")
        log_to_firebase("error", f"Download failed: {e}")
        sys.exit(1)

# Ekstrak miner
def extract_miner():
    logger.info("Extracting miner...")
    try:
        with tarfile.open(FILENAME, "r:gz") as tar:
            tar.extractall()
        if os.path.exists(EXTRACTED_BIN):
            os.rename(EXTRACTED_BIN, RENAMED_BIN)
            os.chmod(RENAMED_BIN, 0o755)
            log_to_firebase("extract", "Miner extracted successfully")
        else:
            logger.error("Extracted binary not found!")
            log_to_firebase("error", "Extracted binary not found")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to extract miner: {e}")
        log_to_firebase("error", f"Extraction failed: {e}")
        sys.exit(1)

# Anti suspend: Restart miner jika terhenti
def run_miner_with_restart():
    global miner_process
    while True:
        logger.info(f"Starting miner at {datetime.datetime.now()}")
        logger.info(f"Using {THREADS} threads")
        log_to_firebase("start", f"Miner started with {THREADS} threads")
        send_fcm_notification("Miner Started", f"Mining started with {THREADS} threads")
        
        cmd = [f"./{RENAMED_BIN}", "-a", ALGO, "-o", POOL, "-u", WALLET, "-t", THREADS]
        try:
            miner_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = miner_process.communicate()
            if miner_process.returncode != 0:
                logger.error(f"Miner stopped with error: {stderr}")
                log_to_firebase("error", f"Miner stopped: {stderr}")
                send_fcm_notification("Miner Error", "Miner stopped unexpectedly")
            else:
                logger.info("Miner stopped normally")
                log_to_firebase("stop", "Miner stopped normally")
        except Exception as e:
            logger.error(f"Error running miner: {e}")
            log_to_firebase("error", f"Error running miner: {e}")
            send_fcm_notification("Miner Error", f"Error: {e}")
        
        logger.info("Restarting miner in 10 seconds...")
        time.sleep(10)

# Tangani sinyal untuk dismiss mining
def handle_shutdown(signum, frame):
    logger.info("Received shutdown signal, stopping miner...")
    if 'miner_process' in globals():
        miner_process.terminate()
        try:
            miner_process.wait(timeout=5)
            logger.info("Miner stopped gracefully")
            log_to_firebase("stop", "Miner stopped by user")
            send_fcm_notification("Miner Stopped", "Mining stopped by user")
        except subprocess.TimeoutExpired:
            miner_process.kill()
            logger.warning("Miner forcefully killed")
            log_to_firebase("stop", "Miner forcefully killed")
            send_fcm_notification("Miner Stopped", "Mining forcefully killed")
    sys.exit(0)

if __name__ == "__main__":
    # Daftarkan handler sinyal untuk dismiss mining
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    try:
        initialize_firebase()
        check_dependencies()
        download_miner()
        extract_miner()
        run_miner_with_restart()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        log_to_firebase("error", f"Unexpected error: {e}")
        send_fcm_notification("Miner Error", f"Unexpected error: {e}")
        sys.exit(1)
