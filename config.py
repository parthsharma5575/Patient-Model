import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

PATIENTS_FILE = os.path.join(DATA_DIR, "patients.json")
DOCTORS_FILE = os.path.join(DATA_DIR, "doctors.json")
STAFF_FILE = os.path.join(DATA_DIR, "staff.json")
MEDICATIONS_FILE = os.path.join(DATA_DIR, "medications.json")
APPOINTMENTS_FILE = os.path.join(DATA_DIR, "appointments.json")
PRESCRIPTIONS_FILE = os.path.join(DATA_DIR, "prescriptions.json")
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedback.json")
MED_ORDERS_FILE = os.path.join(DATA_DIR, "med_orders.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)