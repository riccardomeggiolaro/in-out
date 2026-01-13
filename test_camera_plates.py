#!/usr/bin/env python3
"""
Script di test per il sistema di storico targhe telecamere
"""

import sys
import asyncio
from datetime import datetime

# Aggiungi il percorso del progetto
sys.path.insert(0, '/home/user/in-out')

# Import dei moduli necessari
from modules.md_database.md_database import SessionLocal, CameraPlateHistory
from sqlalchemy import desc

def test_database_table():
    """Verifica che la tabella sia stata creata correttamente"""
    print("=" * 60)
    print("Test 1: Verifica creazione tabella camera_plate_history")
    print("=" * 60)

    try:
        db = SessionLocal()
        # Prova a fare una query semplice
        count = db.query(CameraPlateHistory).count()
        print(f"✅ Tabella esistente con {count} record")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def test_add_plates():
    """Test aggiunta targhe e mantenimento limite 5"""
    print("\n" + "=" * 60)
    print("Test 2: Aggiunta targhe e limite 5 per telecamera")
    print("=" * 60)

    try:
        db = SessionLocal()

        # Pulisci i dati di test esistenti
        db.query(CameraPlateHistory).filter(
            CameraPlateHistory.camera_id.in_(['CAM_TEST_1', 'CAM_TEST_2'])
        ).delete()
        db.commit()

        # Aggiungi 7 targhe per CAM_TEST_1 (dovrebbero rimanerne solo 5)
        test_plates_cam1 = ['AB123CD', 'EF456GH', 'IJ789KL', 'MN012OP', 'QR345ST', 'UV678WX', 'YZ901AB']

        print("\nAggiunta 7 targhe per CAM_TEST_1...")
        for i, plate in enumerate(test_plates_cam1, 1):
            new_plate = CameraPlateHistory(
                camera_id='CAM_TEST_1',
                plate=plate,
                timestamp=datetime.now()
            )
            db.add(new_plate)
            db.commit()
            print(f"  {i}. Aggiunta targa: {plate}")

            # Conta e mantieni solo le ultime 5
            plates_count = db.query(CameraPlateHistory).filter(
                CameraPlateHistory.camera_id == 'CAM_TEST_1'
            ).count()

            if plates_count > 5:
                fifth_plate = db.query(CameraPlateHistory.id).filter(
                    CameraPlateHistory.camera_id == 'CAM_TEST_1'
                ).order_by(desc(CameraPlateHistory.timestamp)).offset(4).limit(1).scalar()

                if fifth_plate:
                    deleted = db.query(CameraPlateHistory).filter(
                        CameraPlateHistory.camera_id == 'CAM_TEST_1',
                        CameraPlateHistory.id < fifth_plate
                    ).delete()
                    db.commit()
                    print(f"     → Eliminate {deleted} targhe vecchie (totale: {plates_count - deleted})")

        # Verifica che ne siano rimaste solo 5
        final_count = db.query(CameraPlateHistory).filter(
            CameraPlateHistory.camera_id == 'CAM_TEST_1'
        ).count()

        print(f"\n✅ Totale targhe per CAM_TEST_1: {final_count}")

        # Mostra le targhe rimaste
        remaining_plates = db.query(CameraPlateHistory).filter(
            CameraPlateHistory.camera_id == 'CAM_TEST_1'
        ).order_by(desc(CameraPlateHistory.timestamp)).all()

        print("\nTarghe rimaste (dalla più recente):")
        for i, plate in enumerate(remaining_plates, 1):
            print(f"  {i}. {plate.plate} - {plate.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        # Aggiungi anche targhe per CAM_TEST_2
        print("\nAggiunta 3 targhe per CAM_TEST_2...")
        test_plates_cam2 = ['XX111YY', 'ZZ222WW', 'AA333BB']

        for plate in test_plates_cam2:
            new_plate = CameraPlateHistory(
                camera_id='CAM_TEST_2',
                plate=plate,
                timestamp=datetime.now()
            )
            db.add(new_plate)
            db.commit()
            print(f"  Aggiunta targa: {plate}")

        cam2_count = db.query(CameraPlateHistory).filter(
            CameraPlateHistory.camera_id == 'CAM_TEST_2'
        ).count()

        print(f"\n✅ Totale targhe per CAM_TEST_2: {cam2_count}")

        db.close()

        return final_count == 5 and cam2_count == 3

    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_query_by_camera():
    """Test query delle ultime 5 targhe per telecamera"""
    print("\n" + "=" * 60)
    print("Test 3: Query targhe per telecamera")
    print("=" * 60)

    try:
        db = SessionLocal()

        # Trova tutte le telecamere
        cameras = db.query(CameraPlateHistory.camera_id).distinct().all()

        print(f"\nTrovate {len(cameras)} telecamere nel database\n")

        for (camera_id,) in cameras:
            plates = db.query(CameraPlateHistory).filter(
                CameraPlateHistory.camera_id == camera_id
            ).order_by(desc(CameraPlateHistory.timestamp)).limit(5).all()

            print(f"📹 {camera_id}:")
            for i, plate in enumerate(plates, 1):
                time_str = plate.timestamp.strftime('%H:%M:%S')
                print(f"   {i}. {plate.plate} • {time_str}")
            print()

        db.close()
        print("✅ Query completata con successo")
        return True

    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def cleanup_test_data():
    """Pulisce i dati di test"""
    print("\n" + "=" * 60)
    print("Pulizia dati di test")
    print("=" * 60)

    try:
        db = SessionLocal()
        deleted = db.query(CameraPlateHistory).filter(
            CameraPlateHistory.camera_id.in_(['CAM_TEST_1', 'CAM_TEST_2'])
        ).delete()
        db.commit()
        db.close()
        print(f"✅ Eliminati {deleted} record di test")
        return True
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 Avvio test sistema targhe telecamere\n")

    results = []

    # Esegui i test
    results.append(("Verifica tabella", test_database_table()))
    results.append(("Aggiunta e limite targhe", test_add_plates()))
    results.append(("Query per telecamera", test_query_by_camera()))

    # Opzionale: pulisci i dati di test
    # results.append(("Pulizia dati test", cleanup_test_data()))

    # Riepilogo
    print("\n" + "=" * 60)
    print("RIEPILOGO TEST")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    total_pass = sum(1 for _, r in results if r)
    print(f"\nTotale: {total_pass}/{len(results)} test passati")

    if total_pass == len(results):
        print("\n🎉 Tutti i test sono passati con successo!")
        sys.exit(0)
    else:
        print("\n⚠️  Alcuni test sono falliti")
        sys.exit(1)
