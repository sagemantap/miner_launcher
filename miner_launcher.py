#!/usr/bin/env python3

import subprocess
import os
import shutil
import tarfile
import urllib.request

# Konfigurasi
WALLET = "mbc1q4xd0fvvj53jwwqaljz9kvrwqxxh0wqs5k89a05.Genzo"
POOL = "stratum+tcp://104.248.150.108:9933"
ALGO = "power2b"
THREADS = "(nproc --all)"
URL = "https://github.com/rplant8/cpuminer-opt-rplant/releases/download/5.0.27/cpuminer-opt-linux.tar.gz"
FILENAME = "cpuminer-opt-linux.tar.gz"
EXTRACTED_BIN = "cpuminer-sse2"
RENAMED_BIN = "miner"

def check_dependencies():
    print("[*] Memeriksa dependensi...")
    for cmd in ["wget", "tar", "chmod"]:
        if shutil.which(cmd) is None:
            print(f"[!] Perintah '{cmd}' tidak ditemukan. Silakan install dulu.")
            exit(1)

def download_miner():
    if not os.path.exists(FILENAME):
        print("[*] Mengunduh miner...")
        urllib.request.urlretrieve(URL, FILENAME)
    else:
        print("[*] File sudah ada, lewati unduh.")

def extract_miner():
    print("[*] Mengekstrak miner...")
    with tarfile.open(FILENAME, "r:gz") as tar:
        tar.extractall()
    if os.path.exists(EXTRACTED_BIN):
        os.rename(EXTRACTED_BIN, RENAMED_BIN)
        os.chmod(RENAMED_BIN, 0o755)

def run_miner():
    print("[*] Menjalankan miner...")
    cmd = [f"./{RENAMED_BIN}", "-a", ALGO, "-o", POOL, "-u", WALLET, "-t", THREADS, "--no-color"]
    subprocess.run(cmd)

if __name__ == "__main__":
    check_dependencies()
    download_miner()
    extract_miner()
    run_miner()
