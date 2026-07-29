import json as pyjson
from typing import Union
from datetime import datetime
from langchain_core.tools import tool
import data_manager
import vector_store
import sub_agents


def _int(value: Union[int, str, None]) -> int:
    """Coerce string/int IDs into int safely (fixes Groq sometimes sending IDs as strings)."""
    if value is None or value == "":
        raise ValueError("Missing required ID value.")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid ID value: {value}")


def _float(value: Union[float, int, str, None]) -> float:
    if value is None or value == "":
        raise ValueError("Missing required numeric value.")
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid numeric value: {value}")


def _doctor_has_patient(doctor_id: int, patient_id: int) -> bool:
    """Check if a doctor has ANY appointment (past/present) with this patient."""
    appts = data_manager.get_appointments_by_doctor(doctor_id)
    return any(a["patient_id"] == patient_id for a in appts)


# ================= UTILITY TOOLS =================
@tool
def get_current_datetime() -> str:
    """Get the current real-world date and time. ALWAYS use this tool first whenever the user
    says things like 'today', 'tomorrow', 'now', 'this week' etc. and you need to compute an
    actual date. Never guess or assume the date."""
    now = datetime.now()
    return (f"Current date: {now.strftime('%Y-%m-%d')}, "
            f"Current time: {now.strftime('%H:%M')}, "
            f"Day of week: {now.strftime('%A')}")


@tool
def search_hospital_knowledge(query: str) -> str:
    """Search across hospital records (patients, doctors, staff, medications) using semantic
    search. Use this for general questions about hospital info that other tools don't cover."""
    results = vector_store.search_all(query, n_results=3)
    output = []
    for category, docs in results.items():
        if docs:
            output.append(f"--- {category.upper()} ---")
            output.extend(docs)
    return "\n".join(output) if output else "No relevant information found."


# ================= PATIENT TOOLS =================
@tool
def get_patient_details(patient_id: Union[int, str]) -> str:
    """Get full details of a patient by patient ID."""
    pid = _int(patient_id)
    p = data_manager.get_patient(pid)
    return str(p) if p else f"No patient found with ID {pid}"


@tool
def register_new_patient(name: str, age: Union[int, str], gender: str, contact: str,
                          medical_history: str = "None", allergies: str = "None",
                          blood_group: str = "Unknown") -> str:
    """Register a new patient into the hospital system. Returns the new patient ID."""
    data = {
        "name": name, "age": _int(age), "gender": gender, "contact": contact,
        "medical_history": medical_history, "allergies": allergies, "blood_group": blood_group
    }
    p = data_manager.add_patient(data)
    vector_store.upsert_patient(p)
    return f"Patient registered successfully with Patient ID: {p['patient_id']}"


@tool
def list_all_doctors(speciality: str = "") -> str:
    """List all doctors, optionally filter by speciality (e.g., Cardiology, Orthopedics)."""
    doctors = data_manager.get_doctors()
    if speciality:
        doctors = [d for d in doctors if speciality.lower() in d.get("speciality", "").lower()]
    if not doctors:
        return "No doctors found."
    return "\n".join([f"ID {d['doctor_id']}: Dr. {d['name']} - {d['speciality']} - {d['department']} "
                       f"(Available: {d.get('available_days')}, {d.get('working_hours')})" for d in doctors])


@tool
def check_doctor_availability(doctor_id: Union[int, str], date: str) -> str:
    """Check a doctor's availability and existing appointments for a given date (format YYYY-MM-DD).
    If you don't know today's date, call get_current_datetime first."""
    did = _int(doctor_id)
    doctor = data_manager.get_doctor(did)
    if not doctor:
        return "Doctor not found."
    appts = data_manager.get_appointments_by_doctor(did)
    day_appts = [a for a in appts if a.get("date") == date and a.get("status") != "cancelled"]
    booked_times = [a["time"] for a in day_appts]
    return (f"Dr. {doctor['name']} works {doctor.get('working_hours')} on {doctor.get('available_days')}.\n"
            f"Already booked slots on {date}: {booked_times if booked_times else 'None'}")


@tool
def book_appointment(patient_id: Union[int, str], doctor_id: Union[int, str],
                      date: str, time: str, reason: str) -> str:
    """Book an appointment for a patient with a doctor on a given date (YYYY-MM-DD) and
    time (HH:MM). Checks for conflicts first. If date/time is relative (e.g. 'tomorrow'),
    call get_current_datetime first to compute the actual date."""
    pid, did = _int(patient_id), _int(doctor_id)
    doctor = data_manager.get_doctor(did)
    if not doctor:
        return "Doctor not found."
    patient = data_manager.get_patient(pid)
    if not patient:
        return "Patient not found."
    existing = data_manager.get_appointments_by_doctor(did)
    conflict = [a for a in existing if a.get("date") == date and a.get("time") == time
                and a.get("status") != "cancelled"]
    if conflict:
        return f"Time slot {time} on {date} is already booked for Dr. {doctor['name']}. Choose another slot."
    appt = data_manager.add_appointment({
        "patient_id": pid, "doctor_id": did, "date": date,
        "time": time, "reason": reason
    })
    return f"Appointment booked! ID {appt['appointment_id']} with Dr. {doctor['name']} on {date} at {time}."


@tool
def get_patient_appointments(patient_id: Union[int, str]) -> str:
    """Get all appointments for a patient."""
    pid = _int(patient_id)
    appts = data_manager.get_appointments_by_patient(pid)
    if not appts:
        return "No appointments found."
    out = []
    for a in appts:
        doc = data_manager.get_doctor(a["doctor_id"])
        doc_name = doc["name"] if doc else "Unknown"
        out.append(f"ID {a['appointment_id']}: Dr. {doc_name} on {a['date']} at {a['time']} "
                    f"- Status: {a['status']} - Reason: {a.get('reason')}")
    return "\n".join(out)


@tool
def get_patient_prescriptions(patient_id: Union[int, str]) -> str:
    """Get all approved prescriptions for a patient, including medicine status
    (assigned/given/taken)."""
    pid = _int(patient_id)
    prescriptions = data_manager.get_prescriptions_by_patient(pid)
    out = []
    for p in prescriptions:
        if p.get("status") != "approved":
            continue
        meds = ", ".join([f"{m['name']} ({m['dosage']}, {m['frequency']}, {m['duration']}) - {m['status']}"
                           for m in p.get("medicines", [])])
        out.append(f"Prescription {p['prescription_id']} (Diagnosis: {p.get('diagnosis')}): {meds}")
    return "\n".join(out) if out else "No approved prescriptions found."


@tool
def mark_medicine_taken(prescription_id: Union[int, str], medicine_name: str) -> str:
    """Mark a medicine in a prescription as taken by the patient."""
    result = data_manager.update_medicine_status(_int(prescription_id), medicine_name, "taken")
    return f"Marked {medicine_name} as taken." if result else "Could not find that prescription/medicine."


@tool
def submit_patient_feedback(patient_id: Union[int, str], feedback_text: str,
                             wants_followup: bool = False) -> str:
    """Submit feedback from a patient about their treatment, and indicate if they want a
    follow-up appointment."""
    data_manager.add_feedback({
        "patient_id": _int(patient_id), "feedback_text": feedback_text,
        "wants_followup": wants_followup, "status": "received"
    })
    msg = "Thank you! Your feedback has been recorded."
    if wants_followup:
        msg += " A follow-up will be arranged - I can help you book one now."
    return msg


# ================= DOCTOR TOOLS =================
@tool
def get_doctor_schedule(doctor_id: Union[int, str]) -> str:
    """Get all appointments scheduled for a doctor."""
    did = _int(doctor_id)
    appts = data_manager.get_appointments_by_doctor(did)
    if not appts:
        return "No appointments scheduled."
    out = []
    for a in appts:
        patient = data_manager.get_patient(a["patient_id"])
        p_name = patient["name"] if patient else "Unknown"
        out.append(f"ID {a['appointment_id']}: Patient {p_name} (ID {a['patient_id']}) on "
                    f"{a['date']} at {a['time']} - Status: {a['status']} - Reason: {a.get('reason')}")
    return "\n".join(out)


@tool
def modify_appointment(appointment_id: Union[int, str], new_date: str = "",
                        new_time: str = "", new_status: str = "") -> str:
    """Modify an appointment's date, time, or status (scheduled/completed/cancelled).
    Leave a field blank ("") to keep it unchanged."""
    aid = _int(appointment_id)
    updates = {}
    if new_date:
        updates["date"] = new_date
    if new_time:
        updates["time"] = new_time
    if new_status:
        updates["status"] = new_status
    if not updates:
        return "No changes provided."
    result = data_manager.update_appointment(aid, updates)
    return f"Appointment {aid} updated: {updates}" if result else "Appointment not found."


@tool
def get_patient_full_history(doctor_id: Union[int, str], patient_id: Union[int, str]) -> str:
    """Get a patient's medical history, past appointments and prescriptions for doctor review.
    ACCESS RESTRICTED: only allowed if this patient has an appointment (past or scheduled)
    with this doctor."""
    did, pid = _int(doctor_id), _int(patient_id)
    if not _doctor_has_patient(did, pid):
        return ("Access denied: This patient does not have any appointment with you. "
                "You can only view history/records of your own patients.")
    patient = data_manager.get_patient(pid)
    if not patient:
        return "Patient not found."
    appts = data_manager.get_appointments_by_patient(pid)
    prescriptions = data_manager.get_prescriptions_by_patient(pid)
    out = [f"Patient: {patient['name']}, Age {patient['age']}, Gender {patient['gender']}",
           f"Medical History: {patient.get('medical_history')}",
           f"Allergies: {patient.get('allergies')}",
           f"Total appointments: {len(appts)}, Total prescriptions: {len(prescriptions)}"]
    return "\n".join(out)


@tool
def suggest_prescription_for_patient(doctor_id: Union[int, str], patient_id: Union[int, str],
                                      diagnosis: str) -> str:
    """Generate an AI-suggested prescription draft for a patient based on diagnosis.
    ACCESS RESTRICTED: only allowed if this patient has an appointment with this doctor.
    This is only a suggestion; doctor must review/modify and then call approve_prescription."""
    did, pid = _int(doctor_id), _int(patient_id)
    if not _doctor_has_patient(did, pid):
        return ("Access denied: This patient does not have any appointment with you. "
                "You cannot suggest a prescription for a patient who isn't yours.")
    patient = data_manager.get_patient(pid)
    if not patient:
        return "Patient not found."
    history = patient.get("medical_history", "None")
    suggestion = sub_agents.suggest_prescription(diagnosis, history)
    return f"AI SUGGESTED PRESCRIPTION (needs your approval/modification):\n{suggestion}"


@tool
def approve_prescription(patient_id: Union[int, str], doctor_id: Union[int, str], diagnosis: str,
                          medicines_json: str, appointment_id: Union[int, str] = 0) -> str:
    """Approve and save the FINAL prescription for a patient after doctor review.
    ACCESS RESTRICTED: only allowed if this patient has an appointment with this doctor.
    medicines_json must be a JSON string list like:
    [{"name": "Paracetamol", "dosage": "500mg", "frequency": "twice daily", "duration": "5 days"}]"""
    pid, did = _int(patient_id), _int(doctor_id)
    if not _doctor_has_patient(did, pid):
        return ("Access denied: This patient does not have any appointment with you. "
                "You cannot approve a prescription for a patient who isn't yours.")
    try:
        medicines = pyjson.loads(medicines_json)
    except Exception:
        return "Invalid medicines format. Provide a valid JSON list string."
    for m in medicines:
        m.setdefault("status", "assigned")
    data = {
        "patient_id": pid, "doctor_id": did, "diagnosis": diagnosis,
        "medicines": medicines, "status": "approved",
        "appointment_id": _int(appointment_id) if appointment_id else 0
    }
    p = data_manager.add_prescription(data)
    return f"Prescription {p['prescription_id']} approved and assigned to patient {pid}."


# ================= STAFF TOOLS =================
@tool
def get_inventory_status() -> str:
    """Get current medication inventory status including stock levels."""
    meds = data_manager.get_medications()
    if not meds:
        return "No medications in inventory."
    out = []
    for m in meds:
        flag = " (LOW STOCK)" if m.get("stock", 0) <= m.get("reorder_level", 0) else ""
        out.append(f"ID {m['med_id']}: {m['name']} - Stock: {m['stock']}{flag} - {m.get('description','')}")
    return "\n".join(out)


@tool
def add_new_medication(name: str, description: str, category: str, stock: Union[int, str],
                        reorder_level: Union[int, str], price: Union[float, str]) -> str:
    """Add a new medication to inventory with its description. This updates the RAG
    knowledge base in real time."""
    m = data_manager.add_medication({
        "name": name, "description": description, "category": category,
        "stock": _int(stock), "reorder_level": _int(reorder_level), "price": _float(price)
    })
    vector_store.upsert_medication(m)
    return f"Medication '{name}' added with ID {m['med_id']}."


@tool
def update_medication_stock(med_id: Union[int, str], new_stock: Union[int, str]) -> str:
    """Update the stock quantity of a medication."""
    m = data_manager.update_medication(_int(med_id), {"stock": _int(new_stock)})
    if m:
        vector_store.upsert_medication(m)
        return f"Stock for {m['name']} updated to {new_stock}."
    return "Medication not found."


@tool
def request_medication_order(med_id: Union[int, str], quantity: Union[int, str],
                              requested_by: str) -> str:
    """Request an order for more medication stock (needs approval)."""
    mid = _int(med_id)
    med = data_manager.get_medication(mid)
    if not med:
        return "Medication not found."
    order = data_manager.add_med_order({
        "med_id": mid, "med_name": med["name"], "quantity": _int(quantity), "requested_by": requested_by
    })
    return f"Order request {order['order_id']} created for {quantity} units of {med['name']}. Pending approval."


@tool
def approve_medication_order(order_id: Union[int, str]) -> str:
    """Approve a pending medication order and update stock accordingly."""
    oid = _int(order_id)
    orders = data_manager.get_med_orders()
    order = next((o for o in orders if o["order_id"] == oid), None)
    if not order:
        return "Order not found."
    if order["status"] == "approved":
        return "Order already approved."
    med = data_manager.get_medication(order["med_id"])
    new_stock = med.get("stock", 0) + order["quantity"]
    data_manager.update_medication(med["med_id"], {"stock": new_stock})
    vector_store.upsert_medication(data_manager.get_medication(med["med_id"]))
    data_manager.update_med_order(oid, {"status": "approved"})
    return f"Order {oid} approved. {med['name']} stock updated to {new_stock}."


@tool
def get_pending_medication_orders() -> str:
    """Get all pending medication orders awaiting approval."""
    orders = [o for o in data_manager.get_med_orders() if o["status"] == "pending_approval"]
    if not orders:
        return "No pending orders."
    return "\n".join([f"Order {o['order_id']}: {o['quantity']}x {o['med_name']} "
                       f"requested by {o['requested_by']}" for o in orders])


@tool
def mark_medicine_given_to_patient(prescription_id: Union[int, str], medicine_name: str) -> str:
    """Mark a medicine from a prescription as GIVEN to the patient by staff.
    Also deducts one unit from inventory."""
    pid = _int(prescription_id)
    result = data_manager.update_medicine_status(pid, medicine_name, "given")
    if not result:
        return "Prescription or medicine not found."
    med = data_manager.get_medication_by_name(medicine_name)
    if med:
        new_stock = max(0, med.get("stock", 0) - 1)
        data_manager.update_medication(med["med_id"], {"stock": new_stock})
        vector_store.upsert_medication(data_manager.get_medication(med["med_id"]))
    return f"Marked {medicine_name} as given for prescription {pid}."


@tool
def get_all_patients_list() -> str:
    """Get a list of all registered patients."""
    patients = data_manager.get_patients()
    if not patients:
        return "No patients registered."
    return "\n".join([f"ID {p['patient_id']}: {p['name']}, Age {p['age']}, Contact {p.get('contact')}"
                       for p in patients])


@tool
def send_feedback_request(patient_id: Union[int, str], treatment_summary: str) -> str:
    """Send a follow-up feedback request message to a patient after treatment."""
    pid = _int(patient_id)
    patient = data_manager.get_patient(pid)
    if not patient:
        return "Patient not found."
    message = sub_agents.draft_feedback_message(patient["name"], treatment_summary)
    data_manager.add_feedback({
        "patient_id": pid, "message": message,
        "treatment_summary": treatment_summary, "status": "pending"
    })
    return f"Feedback request sent to {patient['name']}: {message}"


# ================= TOOL GROUPS =================
patient_tools = [
    get_current_datetime, search_hospital_knowledge, get_patient_details, list_all_doctors,
    check_doctor_availability, book_appointment, get_patient_appointments,
    get_patient_prescriptions, mark_medicine_taken, submit_patient_feedback,
    register_new_patient
]

doctor_tools = [
    get_current_datetime, search_hospital_knowledge, get_doctor_schedule, modify_appointment,
    get_patient_full_history, suggest_prescription_for_patient, approve_prescription,
    get_patient_details
]

staff_tools = [
    get_current_datetime, search_hospital_knowledge, get_inventory_status, add_new_medication,
    update_medication_stock, request_medication_order, approve_medication_order,
    get_pending_medication_orders, mark_medicine_given_to_patient, get_all_patients_list,
    register_new_patient, send_feedback_request, get_patient_details
]