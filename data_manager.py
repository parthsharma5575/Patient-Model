import json
import os
import threading
from datetime import datetime
import config

_lock = threading.Lock()


def _load(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save(file_path, data):
    with _lock:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)


def _next_id(records, key):
    if not records:
        return 1
    return max(r.get(key, 0) for r in records) + 1


# ---------------- Patients ----------------
def get_patients():
    return _load(config.PATIENTS_FILE)


def get_patient(patient_id):
    for p in get_patients():
        if p["patient_id"] == patient_id:
            return p
    return None


def add_patient(data):
    patients = get_patients()
    new_id = _next_id(patients, "patient_id")
    data["patient_id"] = new_id
    data.setdefault("created_at", datetime.now().isoformat())
    patients.append(data)
    _save(config.PATIENTS_FILE, patients)
    return data


def update_patient(patient_id, updates):
    patients = get_patients()
    for p in patients:
        if p["patient_id"] == patient_id:
            p.update(updates)
            _save(config.PATIENTS_FILE, patients)
            return p
    return None


# ---------------- Doctors ----------------
def get_doctors():
    return _load(config.DOCTORS_FILE)


def get_doctor(doctor_id):
    for d in get_doctors():
        if d["doctor_id"] == doctor_id:
            return d
    return None


def add_doctor(data):
    doctors = get_doctors()
    new_id = _next_id(doctors, "doctor_id")
    data["doctor_id"] = new_id
    doctors.append(data)
    _save(config.DOCTORS_FILE, doctors)
    return data


def update_doctor(doctor_id, updates):
    doctors = get_doctors()
    for d in doctors:
        if d["doctor_id"] == doctor_id:
            d.update(updates)
            _save(config.DOCTORS_FILE, doctors)
            return d
    return None


# ---------------- Staff ----------------
def get_staff():
    return _load(config.STAFF_FILE)


def get_staff_member(staff_id):
    for s in get_staff():
        if s["staff_id"] == staff_id:
            return s
    return None


def add_staff(data):
    staff = get_staff()
    new_id = _next_id(staff, "staff_id")
    data["staff_id"] = new_id
    staff.append(data)
    _save(config.STAFF_FILE, staff)
    return data


# ---------------- Medications ----------------
def get_medications():
    return _load(config.MEDICATIONS_FILE)


def get_medication(med_id):
    for m in get_medications():
        if m["med_id"] == med_id:
            return m
    return None


def get_medication_by_name(name):
    for m in get_medications():
        if m["name"].lower() == name.lower():
            return m
    return None


def add_medication(data):
    meds = get_medications()
    new_id = _next_id(meds, "med_id")
    data["med_id"] = new_id
    meds.append(data)
    _save(config.MEDICATIONS_FILE, meds)
    return data


def update_medication(med_id, updates):
    meds = get_medications()
    for m in meds:
        if m["med_id"] == med_id:
            m.update(updates)
            _save(config.MEDICATIONS_FILE, meds)
            return m
    return None


# ---------------- Appointments ----------------
def get_appointments():
    return _load(config.APPOINTMENTS_FILE)


def get_appointment(appointment_id):
    for a in get_appointments():
        if a["appointment_id"] == appointment_id:
            return a
    return None


def get_appointments_by_patient(patient_id):
    return [a for a in get_appointments() if a["patient_id"] == patient_id]


def get_appointments_by_doctor(doctor_id):
    return [a for a in get_appointments() if a["doctor_id"] == doctor_id]


def add_appointment(data):
    appts = get_appointments()
    new_id = _next_id(appts, "appointment_id")
    data["appointment_id"] = new_id
    data.setdefault("status", "scheduled")
    data.setdefault("created_at", datetime.now().isoformat())
    appts.append(data)
    _save(config.APPOINTMENTS_FILE, appts)
    return data


def update_appointment(appointment_id, updates):
    appts = get_appointments()
    for a in appts:
        if a["appointment_id"] == appointment_id:
            a.update(updates)
            _save(config.APPOINTMENTS_FILE, appts)
            return a
    return None


# ---------------- Prescriptions ----------------
def get_prescriptions():
    return _load(config.PRESCRIPTIONS_FILE)


def get_prescriptions_by_patient(patient_id):
    return [p for p in get_prescriptions() if p["patient_id"] == patient_id]


def add_prescription(data):
    prescriptions = get_prescriptions()
    new_id = _next_id(prescriptions, "prescription_id")
    data["prescription_id"] = new_id
    data.setdefault("created_at", datetime.now().isoformat())
    data.setdefault("status", "approved")
    prescriptions.append(data)
    _save(config.PRESCRIPTIONS_FILE, prescriptions)
    return data


def update_prescription(prescription_id, updates):
    prescriptions = get_prescriptions()
    for p in prescriptions:
        if p["prescription_id"] == prescription_id:
            p.update(updates)
            _save(config.PRESCRIPTIONS_FILE, prescriptions)
            return p
    return None


def update_medicine_status(prescription_id, med_name, status):
    prescriptions = get_prescriptions()
    found = None
    for p in prescriptions:
        if p["prescription_id"] == prescription_id:
            for m in p.get("medicines", []):
                if m["name"].lower() == med_name.lower():
                    m["status"] = status
                    found = p
            if found:
                _save(config.PRESCRIPTIONS_FILE, prescriptions)
    return found


# ---------------- Feedback ----------------
def get_feedback():
    return _load(config.FEEDBACK_FILE)


def add_feedback(data):
    feedback = get_feedback()
    new_id = _next_id(feedback, "feedback_id")
    data["feedback_id"] = new_id
    data.setdefault("created_at", datetime.now().isoformat())
    feedback.append(data)
    _save(config.FEEDBACK_FILE, feedback)
    return data


def get_pending_feedback_requests(patient_id):
    return [f for f in get_feedback()
            if f["patient_id"] == patient_id and f.get("status") == "pending"]


def update_feedback(feedback_id, updates):
    feedback = get_feedback()
    for f in feedback:
        if f["feedback_id"] == feedback_id:
            f.update(updates)
            _save(config.FEEDBACK_FILE, feedback)
            return f
    return None


# ---------------- Medication Orders ----------------
def get_med_orders():
    return _load(config.MED_ORDERS_FILE)


def add_med_order(data):
    orders = get_med_orders()
    new_id = _next_id(orders, "order_id")
    data["order_id"] = new_id
    data.setdefault("status", "pending_approval")
    data.setdefault("created_at", datetime.now().isoformat())
    orders.append(data)
    _save(config.MED_ORDERS_FILE, orders)
    return data


def update_med_order(order_id, updates):
    orders = get_med_orders()
    for o in orders:
        if o["order_id"] == order_id:
            o.update(updates)
            _save(config.MED_ORDERS_FILE, orders)
            return o
    return None