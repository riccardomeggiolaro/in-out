import os
import shutil
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = "dist"

CONFIG_FILE = "config.json"
STATIC_DIR = os.path.join("application", "static")

EXCLUDE_DIRS = ["dist", ".venv", "__pycache__", ".git"]

def clean_dist():
    if os.path.exists(DIST_DIR):
        print("🧹 Pulizia dist...")
        shutil.rmtree(DIST_DIR)

def run_pyarmor():
    print("🔐 Offuscazione con PyArmor v7...")

    cmd = ["pyarmor", "obfuscate", "-r"]

    for ex in EXCLUDE_DIRS:
        cmd.extend(["--exclude", ex])

    cmd.append(PROJECT_DIR)

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("❌ Errore PyArmor")
        sys.exit(1)

    print("✅ Offuscazione completata")

def copy_files():
    print("📁 Copia file statici e config...")

    src_config = os.path.join(PROJECT_DIR, CONFIG_FILE)
    dst_config = os.path.join(DIST_DIR, CONFIG_FILE)

    if os.path.exists(src_config):
        shutil.copy(src_config, dst_config)

    src_static = os.path.join(PROJECT_DIR, STATIC_DIR)
    dst_static = os.path.join(DIST_DIR, STATIC_DIR)

    if os.path.exists(src_static):
        shutil.copytree(src_static, dst_static, dirs_exist_ok=True)

if __name__ == "__main__":
    print("🚀 BUILD START\n")

    clean_dist()
    run_pyarmor()

    print("\n🔄 Copy files...")
    copy_files()

    print("\n✅ BUILD COMPLETATA")