#!/bin/bash

##############################################################################
# Script di test per il sincronizzatore
# Crea un ambiente di prova per testare il funzionamento
##############################################################################

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Test Sincronizzatore Cartelle                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Crea cartelle di test
TEST_DIR="/tmp/sync_test"
LOCAL_DIR="$TEST_DIR/local"
REMOTE_DIR="$TEST_DIR/remote"

echo "🧹 Pulizia ambiente di test precedente..."
rm -rf "$TEST_DIR"

echo "📁 Creazione cartelle di test..."
mkdir -p "$LOCAL_DIR"
mkdir -p "$REMOTE_DIR"

echo "✅ Ambiente di test creato"
echo "   Locale: $LOCAL_DIR"
echo "   Remoto: $REMOTE_DIR"
echo ""

# Avvia il sincronizzatore in background
echo "🚀 Avvio sincronizzatore..."

# Crea una versione di test dello script con output ridotto
TEST_SCRIPT="/tmp/sync_test.sh"

# Determina il percorso dello script sync_folder.sh
if [ -f "./sync_folder.sh" ]; then
    SYNC_SCRIPT="./sync_folder.sh"
elif [ -f "$HOME/.local/bin/sync_folder.sh" ]; then
    SYNC_SCRIPT="$HOME/.local/bin/sync_folder.sh"
else
    echo "❌ Script sync_folder.sh non trovato"
    exit 1
fi

# Avvia il sincronizzatore in background con output su file
"$SYNC_SCRIPT" "$LOCAL_DIR" "$REMOTE_DIR" > /tmp/sync_test.log 2>&1 &
SYNC_PID=$!

echo "✅ Sincronizzatore avviato (PID: $SYNC_PID)"
echo ""

# Attendi che sia pronto
sleep 2

# Test 1: Copia di file singolo
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Test 1: File Singolo                                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📝 Creazione file di test..."
echo "Contenuto di test" > "$LOCAL_DIR/file_test.txt"

echo "⏳ Attesa sincronizzazione (5 secondi)..."
sleep 5

if [ ! -f "$LOCAL_DIR/file_test.txt" ] && [ -f "$REMOTE_DIR/file_test.txt" ]; then
    echo "✅ Test 1 PASSATO - File sincronizzato e eliminato dalla locale"
    echo "   Locale: $(ls $LOCAL_DIR 2>/dev/null | wc -l) file"
    echo "   Remoto: $(ls $REMOTE_DIR 2>/dev/null | wc -l) file"
else
    echo "❌ Test 1 FALLITO"
    echo "   File locale esiste: $([ -f "$LOCAL_DIR/file_test.txt" ] && echo "SI" || echo "NO")"
    echo "   File remoto esiste: $([ -f "$REMOTE_DIR/file_test.txt" ] && echo "SI" || echo "NO")"
fi
echo ""

# Test 2: Sottocartelle
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Test 2: Sottocartelle                                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📁 Creazione sottocartelle..."
mkdir -p "$LOCAL_DIR/documenti"
echo "File in sottocartella" > "$LOCAL_DIR/documenti/documento.txt"

echo "⏳ Attesa sincronizzazione (5 secondi)..."
sleep 5

if [ ! -f "$LOCAL_DIR/documenti/documento.txt" ] && [ -f "$REMOTE_DIR/documenti/documento.txt" ]; then
    echo "✅ Test 2 PASSATO - Sottocartelle sincronizzate"
else
    echo "❌ Test 2 FALLITO"
fi
echo ""

# Test 3: File multipli
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Test 3: File Multipli                                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📝 Creazione file multipli..."
for i in {1..5}; do
    echo "File numero $i" > "$LOCAL_DIR/file_$i.txt"
done

echo "⏳ Attesa sincronizzazione (10 secondi)..."
sleep 10

LOCAL_COUNT=$(ls "$LOCAL_DIR" 2>/dev/null | wc -l)
REMOTE_COUNT=$(find "$REMOTE_DIR" -type f 2>/dev/null | wc -l)

echo "   File nella locale: $LOCAL_COUNT"
echo "   File nella remota: $REMOTE_COUNT"

if [ "$LOCAL_COUNT" -lt 3 ] && [ "$REMOTE_COUNT" -gt 3 ]; then
    echo "✅ Test 3 PASSATO - File multipli sincronizzati"
else
    echo "❌ Test 3 FALLITO"
fi
echo ""

# Test 4: File di grandi dimensioni
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Test 4: File Grande (10 MB)                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📝 Creazione file di 10 MB..."
dd if=/dev/zero of="$LOCAL_DIR/file_grande.bin" bs=1M count=10 2>/dev/null

echo "⏳ Attesa sincronizzazione (15 secondi)..."
sleep 15

if [ ! -f "$LOCAL_DIR/file_grande.bin" ] && [ -f "$REMOTE_DIR/file_grande.bin" ]; then
    echo "✅ Test 4 PASSATO - File grande sincronizzato"
    REMOTE_SIZE=$(stat -f%z "$REMOTE_DIR/file_grande.bin" 2>/dev/null || stat -c%s "$REMOTE_DIR/file_grande.bin" 2>/dev/null)
    echo "   Dimensione nella remota: $(numfmt --to=iec-i --suffix=B $REMOTE_SIZE 2>/dev/null || echo "$REMOTE_SIZE bytes")"
else
    echo "❌ Test 4 FALLITO"
fi
echo ""

# Arresta il sincronizzatore
echo "🛑 Arresto sincronizzatore..."
kill $SYNC_PID 2>/dev/null || true
sleep 1

# Riepilogo
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Riepilogo                                                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 Stato finale:"
echo "   File nella cartella locale: $(find "$LOCAL_DIR" -type f 2>/dev/null | wc -l)"
echo "   File nella cartella remota: $(find "$REMOTE_DIR" -type f 2>/dev/null | wc -l)"
echo ""

echo "📋 Log del sincronizzatore:"
echo "   Percorso: /tmp/sync_test.log"
echo "   Righe: $(wc -l < /tmp/sync_test.log)"
echo ""

echo "🧹 Pulizia..."
read -p "Vuoi rimuovere le cartelle di test? (y/n) [n]: " pulisci
if [ "$pulisci" = "y" ] || [ "$pulisci" = "Y" ]; then
    rm -rf "$TEST_DIR"
    rm -f /tmp/sync_test.log /tmp/sync_state.db
    echo "✅ Pulizia completata"
else
    echo "ℹ️  Cartelle di test conservate in: $TEST_DIR"
    echo "   Log in: /tmp/sync_test.log"
    echo ""
    echo "Per esaminare il log:"
    echo "   cat /tmp/sync_test.log"
    echo ""
    echo "Per ripulire manualmente:"
    echo "   rm -rf $TEST_DIR"
fi
echo ""

echo "✅ Test completato"
