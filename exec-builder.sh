#/usr/bin/bash
source venv/bin/activate
pip install -r requirements.txt
# Linux
pyinstaller --onefile --add-data "config.json:." --add-data "service.log:."  main.py
# Windows
python -m PyInstaller --onefile --add-data "config.json:." --add-data "service.log:."  main.py
./dist/main