#!/bin/bash
source .venv/bin/activate
pip install -r requirements.txt
# Linux
pyinstaller --onefile \
    --add-data "config.json:." \
    --add-data "service.log:." \
    --add-data "client/dashboard.html:./client/" \
    --add-data "client/index.html:./client/" \
    main.py
# Windows
python -m PyInstaller --onefile \
    --add-data "config.json:." \
    --add-data "service.log:." \
    --add-data "client/dashboard.html:./client/" \
    --add-data "client/index.html:./client/" \
    main.py

./dist/main