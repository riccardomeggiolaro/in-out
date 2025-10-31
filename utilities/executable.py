#!/usr/bin/env python3
"""
Script per creare un eseguibile standalone usando PyInstaller
Usage: python executable.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_virtual_env():
    """Controlla se siamo in un ambiente virtuale"""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Attenzione: Non sei in un ambiente virtuale!")
        response = input("Continuare comunque? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)

def install_requirements():
    """Installa le dipendenze da requirements.txt"""
    if os.path.exists('requirements.txt'):
        print("📦 Installando dipendenze...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         check=True, capture_output=True, text=True)
            print("✅ Dipendenze installate con successo")
        except subprocess.CalledProcessError as e:
            print(f"❌ Errore nell'installazione delle dipendenze: {e}")
            print(f"Output: {e.stdout}")
            print(f"Error: {e.stderr}")
            sys.exit(1)
    else:
        print("⚠️  File requirements.txt non trovato")

def clean_previous_builds():
    """Pulisce build e dist precedenti"""
    print("🧹 Pulizia build precedenti...")
    for folder in ['build', 'dist', '__pycache__']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"  Rimossa cartella: {folder}")
    
    # Rimuovi file .spec se esistono
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"  Rimosso file: {spec_file}")

def generate_pyinstaller_command():
    """Genera il comando PyInstaller con tutti i parametri"""
    cmd = [
        'pyinstaller',
        '--onefile',
        '--name', 'in-out'  # Nome dell'eseguibile
    ]
    
    # File statici obbligatori
    static_files = [
        ('config.json', '.'),
        ('service.log', '.')
    ]
    
    for src, dst in static_files:
        if os.path.exists(src):
            cmd.extend(['--add-data', f'{src}:{dst}'])
            print(f"  Aggiunto file: {src} -> {dst}")
        else:
            print(f"⚠️  File non trovato: {src}")
    
    # Aggiungi dinamicamente cartelle con file statici
    resource_dirs = [
        ('applications/static', './applications/static'),
        ('static', './static'),
        ('reports', './reports')  # Cartella reports con file HTML
    ]
    
    for src_dir, dst_dir in resource_dirs:
        if os.path.exists(src_dir):
            print(f"📁 Scansione cartella: {src_dir}")
            
            # Aggiungi tutta la cartella
            cmd.extend(['--add-data', f'{src_dir}:{dst_dir}'])
            print(f"  Aggiunta intera cartella: {src_dir} -> {dst_dir}")
            
            # Conta i file per informazione
            file_count = 0
            html_count = 0
            for root, dirs, files in os.walk(src_dir):
                file_count += len(files)
                html_count += len([f for f in files if f.endswith(('.html', '.htm'))])
            
            print(f"  Trovati {file_count} file totali")
            if html_count > 0:
                print(f"  Trovati {html_count} file HTML")
        else:
            print(f"⚠️  Cartella non trovata: {src_dir}")
    
    # Aggiungi opzioni aggiuntive
    cmd.extend([
        '--clean',  # Pulisci cache
        '--noconfirm',  # Non chiedere conferma per sovrascrivere
        '--hidden-import=tkinter',  # Include tkinter per l'interfaccia desktop
        '--hidden-import=tkinter.ttk',  # Include ttk per stili moderni
        '--hidden-import=tkinter.messagebox',  # Include messagebox per errori
        '--collect-all=tkinter',  # Include tutto tkinter
        # '--windowed',  # Decommentare per app GUI (nasconde console)
        # '--icon=icon.ico',  # Decommentare se hai un'icona
    ])
    
    # File principale
    main_files = ['main.py', 'app.py', 'run.py']
    main_file = None
    
    for file in main_files:
        if os.path.exists(file):
            main_file = file
            break
    
    if main_file:
        cmd.append(main_file)
        print(f"📄 File principale: {main_file}")
    else:
        print("❌ Nessun file principale trovato (main.py, app.py, run.py)")
        sys.exit(1)
    
    return cmd

def run_pyinstaller(cmd):
    """Esegue PyInstaller"""
    print("\n🚀 Avvio PyInstaller...")
    print(f"Comando: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True, text=True)
        print("✅ Build completata con successo!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore durante la build: {e}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller non trovato. Installalo con: pip install pyinstaller")
        return False

def check_executable():
    """Controlla se l'eseguibile è stato creato"""
    executable_path = None
    
    if os.path.exists('dist'):
        # Cerca l'eseguibile
        for file in os.listdir('dist'):
            if os.path.isfile(os.path.join('dist', file)):
                executable_path = os.path.join('dist', file)
                break
    
    if executable_path and os.path.exists(executable_path):
        file_size = os.path.getsize(executable_path) / (1024 * 1024)  # MB
        print(f"📦 Eseguibile creato: {executable_path}")
        print(f"📏 Dimensione: {file_size:.1f} MB")
        
        # Rendi eseguibile su Linux/Mac
        if os.name != 'nt':  # Non Windows
            os.chmod(executable_path, 0o755)
            print("🔧 Permessi di esecuzione impostati")
        
        return executable_path
    else:
        print("❌ Eseguibile non trovato!")
        return None

def run_executable(executable_path):
    """Chiede se eseguire l'applicazione"""
    response = input(f"\n🎯 Vuoi eseguire l'applicazione? (y/N): ")
    if response.lower() == 'y':
        print(f"▶️  Eseguendo {executable_path}...")
        try:
            if os.name == 'nt':  # Windows
                subprocess.run([executable_path])
            else:  # Linux/Mac
                subprocess.run([f'./{executable_path}'])
        except KeyboardInterrupt:
            print("\n⏹️  Esecuzione interrotta")
        except Exception as e:
            print(f"❌ Errore nell'esecuzione: {e}")

def main():
    """Funzione principale"""
    print("🔧 PyInstaller Build Script")
    print("=" * 30)
    
    # 1. Controlla ambiente virtuale
    check_virtual_env()
    
    # 2. Installa dipendenze
    install_requirements()
    
    # 3. Pulisci build precedenti
    clean_previous_builds()
    
    # 4. Genera comando PyInstaller
    cmd = generate_pyinstaller_command()
    
    # 5. Esegui PyInstaller
    if run_pyinstaller(cmd):
        # 6. Controlla risultato
        executable_path = check_executable()
        
        if executable_path:
            # 7. Opzionalmente esegui l'app
            run_executable(executable_path)
            
            print(f"\n🎉 Processo completato!")
            print(f"📁 Eseguibile disponibile in: {executable_path}")
        else:
            sys.exit(1)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()