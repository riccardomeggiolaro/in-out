import requests
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor

BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInBhc3N3b3JkIjoiJDJiJDEyJFBBSEU0a2g2bG5YbzN3OVNGOXRqN08xNHJJRi4zMzQzRUQyMFlsWkN0THNhb1BGWWV2dlRPIiwibGV2ZWwiOjMsImRlc2NyaXB0aW9uIjoiQWRtaW5pc3RyYXRvciIsInByaW50ZXJfbmFtZSI6bnVsbCwiZGF0ZV9jcmVhdGVkIjpudWxsLCJleHAiOjE3NDM3ODIzMDJ9.RW9sQW4BO_semIs3CPZ31EYNhwqt3aaeisnuh_qYWi0"

# Configurazione
API_URL = "http://localhost:8000/anagrafic/deselect/subject/1"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

def make_request(request_id):
    """Effettua una chiamata API e salva il risultato"""
    start = time.time()
    print(f"[{request_id}] Avvio richiesta @ {start:.4f}")
    
    try:
        response = requests.get(API_URL, headers=HEADERS)
        elapsed = time.time() - start
        
        try:
            response_data = response.json()
        except:
            response_data = response.text
            
        print(f"[{request_id}] Risposta ricevuta dopo {elapsed:.4f}s - Status: {response.status_code}")
        return {
            "status_code": response.status_code,
            "data": response_data,
            "headers": dict(response.headers),
            "start_time": start,
            "end_time": time.time()
        }
        
    except Exception as e:
        print(f"[{request_id}] Errore dopo {time.time() - start:.4f}s: {str(e)}")
        return {
            "error": str(e),
            "start_time": start,
            "end_time": time.time()
        }

def run_concurrent_test():
    """Esegue due richieste in parallelo usando ThreadPoolExecutor"""
    print("Avvio test di concorrenza...\n")
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Avvia entrambe le richieste contemporaneamente
        future1 = executor.submit(make_request, "request1")
        future2 = executor.submit(make_request, "request2")
        
        # Recupera i risultati
        results = {
            "request1": future1.result(),
            "request2": future2.result()
        }
    
    # Analisi dei risultati
    print("\n===== RISULTATI DEL TEST =====")
    
    # Calcola i tempi
    times = [
        (results["request1"]["start_time"], results["request1"]["end_time"]),
        (results["request2"]["start_time"], results["request2"]["end_time"])
    ]
    
    print(f"Prima richiesta iniziata @ {times[0][0]:.4f}")
    print(f"Seconda richiesta iniziata @ {times[1][0]:.4f}")
    print(f"Differenza di avvio: {abs(times[0][0] - times[1][0]):.4f}s")
    
    # Verifica sovrapposizione
    overlap_start = max(times[0][0], times[1][0])
    overlap_end = min(times[0][1], times[1][1])
    overlapping = overlap_start < overlap_end
    
    print("\n🔍 Analisi concorrenza:")
    print(f"Le richieste si sono sovrapposte per {overlap_end - overlap_start:.4f}s" if overlapping else "Nessuna sovrapposizione effettiva")
    
    # Verifica esito
    success_count = sum(1 for r in results.values() if "status_code" in r and r["status_code"] == 200)
    
    if success_count == 1:
        print("\n✅ TEST SUPERATO: Una richiesta ha avuto successo e l'altra è fallita, come previsto.")
    elif success_count == 0:
        print("\n❌ TEST FALLITO: Entrambe le richieste sono fallite.")
    else:
        print("\n❌ TEST FALLITO: Entrambe le richieste hanno avuto successo, il lock non funziona correttamente.")
    
    # Stampa dettagli
    print("\nDettagli Richiesta 1:")
    print_result_details(results["request1"])
    
    print("\nDettagli Richiesta 2:")
    print_result_details(results["request2"])

def print_result_details(result):
    """Stampa i dettagli di una risposta in modo formattato"""
    if "error" in result:
        print(f"  Errore: {result['error']}")
        print(f"  Tempo: {result['start_time']:.4f} -> {result['end_time']:.4f}")
        return
    
    print(f"  Status code: {result['status_code']}")
    print(f"  Tempo: {result['start_time']:.4f} -> {result['end_time']:.4f}")
    print(f"  Durata: {result['end_time'] - result['start_time']:.4f}s")
    
    if isinstance(result["data"], dict):
        print("  Response data:")
        print(json.dumps(result["data"], indent=2))
    else:
        print(f"  Response text: {result['data']}")

if __name__ == "__main__":
    run_concurrent_test()