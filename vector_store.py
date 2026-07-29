import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import config
import data_manager
_client = None
_collections = {}
_ef = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=config.CHROMA_DIR,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
    return _client
def get_embedding_function():
    global _ef
    if _ef is None:
        _ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=config.EMBEDDING_MODEL
        )
    return _ef


def get_collection(name):
    if name not in _collections:
        client = get_client()
        ef = get_embedding_function()
        _collections[name] = client.get_or_create_collection(name=name, embedding_function=ef)
    return _collections[name]


def _doc_from_patient(p):
    return (f"Patient {p.get('name')}, ID {p['patient_id']}, Age {p.get('age')}, "
            f"Gender {p.get('gender')}, Contact {p.get('contact')}, "
            f"Medical history: {p.get('medical_history', 'None')}, "
            f"Allergies: {p.get('allergies', 'None')}, "
            f"Blood group: {p.get('blood_group', 'Unknown')}")


def _doc_from_doctor(d):
    return (f"Doctor {d.get('name')}, ID {d['doctor_id']}, Speciality {d.get('speciality')}, "
            f"Department {d.get('department')}, Experience {d.get('experience')} years, "
            f"Available days: {d.get('available_days')}, Working hours: {d.get('working_hours')}")


def _doc_from_staff(s):
    return (f"Staff {s.get('name')}, ID {s['staff_id']}, Role {s.get('role')}, "
            f"Department {s.get('department')}, Shift {s.get('shift')}")


def _doc_from_med(m):
    return (f"Medication {m.get('name')}, ID {m['med_id']}, Description: {m.get('description')}, "
            f"Category: {m.get('category')}, Stock: {m.get('stock')}, "
            f"Reorder level: {m.get('reorder_level')}, Price: {m.get('price')}")


def upsert_patient(p):
    col = get_collection("patients")
    col.upsert(ids=[f"patient_{p['patient_id']}"], documents=[_doc_from_patient(p)],
               metadatas=[{"patient_id": p['patient_id'], "type": "patient"}])


def upsert_doctor(d):
    col = get_collection("doctors")
    col.upsert(ids=[f"doctor_{d['doctor_id']}"], documents=[_doc_from_doctor(d)],
               metadatas=[{"doctor_id": d['doctor_id'], "type": "doctor"}])


def upsert_staff(s):
    col = get_collection("staff")
    col.upsert(ids=[f"staff_{s['staff_id']}"], documents=[_doc_from_staff(s)],
               metadatas=[{"staff_id": s['staff_id'], "type": "staff"}])


def upsert_medication(m):
    col = get_collection("medications")
    col.upsert(ids=[f"med_{m['med_id']}"], documents=[_doc_from_med(m)],
               metadatas=[{"med_id": m['med_id'], "type": "medication"}])


def rebuild_all():
    for p in data_manager.get_patients():
        upsert_patient(p)
    for d in data_manager.get_doctors():
        upsert_doctor(d)
    for s in data_manager.get_staff():
        upsert_staff(s)
    for m in data_manager.get_medications():
        upsert_medication(m)


def search(collection_name, query, n_results=3):
    col = get_collection(collection_name)
    count = col.count()
    if count == 0:
        return []
    res = col.query(query_texts=[query], n_results=min(n_results, count))
    return res.get("documents", [[]])[0]


def search_all(query, n_results=3):
    results = {}
    for name in ["patients", "doctors", "staff", "medications"]:
        results[name] = search(name, query, n_results)
    return results