import os
import shutil
import subprocess
import sys

# === CONFIG ===
PROJECT_DIR = "."
DIST_DIR = "dist"

CONFIG_FILE = "config.json"
STATIC_DIR = os.path.join("applications", "static")

EXCLUDE_DIRS = ["dist", ".venv", "__pycache__", ".git", "tmt-cups", "documentations", "utilities"]


# === STEP 0: Pulizia dist ===
def clean_dist():
    if os.path.exists(DIST_DIR):
        print("🧹 Pulizia dist...")
        shutil.rmtree(DIST_DIR)


# === STEP 1: PyArmor ===
def run_pyarmor():
    print("🔐 Offuscazione con PyArmor...")

    cmd = ["pyarmor", "gen", "-r"]

    for ex in EXCLUDE_DIRS:
        cmd.extend(["--exclude", ex])

    cmd.append(PROJECT_DIR)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Errore PyArmor:")
        print(result.stderr)
        sys.exit(1)

    print("✅ Offuscazione completata")


# === STEP 2: Copia file ===
def copy_files():
    print("📁 Copia file statici e config...")

    # Copia config.json
    src_config = os.path.join(PROJECT_DIR, CONFIG_FILE)
    dst_config = os.path.join(DIST_DIR, CONFIG_FILE)

    if os.path.exists(src_config):
        shutil.copy(src_config, dst_config)
        print(f"✔ Copiato {CONFIG_FILE}")
    else:
        print(f"⚠ {CONFIG_FILE} non trovato")

    # Copia cartella static
    src_static = os.path.join(PROJECT_DIR, STATIC_DIR)
    dst_static = os.path.join(DIST_DIR, STATIC_DIR)

    if os.path.exists(src_static):
        shutil.copytree(src_static, dst_static, dirs_exist_ok=True)
        print(f"✔ Copiata cartella {STATIC_DIR}")
    else:
        print(f"⚠ Cartella {STATIC_DIR} non trovata")


# === MAIN ===
if __name__ == "__main__":
    print("🚀 BUILD START\n")
    clean_dist()
    run_pyarmor()
    copy_files()

    print("\n✅ Build completata!")