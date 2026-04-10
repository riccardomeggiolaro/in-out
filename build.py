import os
import shutil
import subprocess
import sys

# === CONFIG ===
PROJECT_DIR = "."
DIST_DIR = os.path.join("dist", ".")

CONFIG_FILE = "config.json"
STATIC_DIR = os.path.join("application", "static")

# === STEP 1: PyArmor ===
def run_pyarmor():
    print("🔐 Offuscazione con PyArmor...")
    
    result = subprocess.run(
        ["pyarmor", "gen", "-r", PROJECT_DIR],
        capture_output=True,
        text=True
    )

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
    run_pyarmor()
    copy_files()

    print("\n🚀 Build completata!")