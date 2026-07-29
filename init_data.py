import data_manager
import vector_store


def init():
    if not data_manager.get_doctors():
        doctors = [
            {"name": "Anita Sharma", "speciality": "Cardiology", "department": "Cardiology",
             "experience": 12, "available_days": "Mon-Fri", "working_hours": "09:00-17:00",
             "contact": "9990001111"},
            {"name": "Rohan Mehta", "speciality": "Orthopedics", "department": "Orthopedics",
             "experience": 8, "available_days": "Mon-Sat", "working_hours": "10:00-18:00",
             "contact": "9990002222"},
            {"name": "Priya Nair", "speciality": "Pediatrics", "department": "Pediatrics",
             "experience": 6, "available_days": "Tue-Sun", "working_hours": "09:00-15:00",
             "contact": "9990003333"},
            {"name": "Vikram Rao", "speciality": "Neurology", "department": "Neurology",
             "experience": 15, "available_days": "Mon-Fri", "working_hours": "11:00-19:00",
             "contact": "9990004444"},
            {"name": "Kavita Iyer", "speciality": "Dermatology", "department": "Dermatology",
             "experience": 5, "available_days": "Wed-Sun", "working_hours": "10:00-16:00",
             "contact": "9990005555"},
            {"name": "Suresh Patel", "speciality": "General Medicine", "department": "General",
             "experience": 20, "available_days": "Mon-Sat", "working_hours": "08:00-14:00",
             "contact": "9990006666"},
        ]
        for d in doctors:
            saved = data_manager.add_doctor(d)
            vector_store.upsert_doctor(saved)

    if not data_manager.get_staff():
        staff = [
            {"name": "Kabir Singh", "role": "Nurse", "department": "General",
             "shift": "Morning", "contact": "8880001111"},
            {"name": "Meena Joshi", "role": "Pharmacist", "department": "Pharmacy",
             "shift": "Evening", "contact": "8880002222"},
            {"name": "Ajay Verma", "role": "Receptionist", "department": "Front Desk",
             "shift": "Morning", "contact": "8880003333"},
            {"name": "Divya Reddy", "role": "Lab Technician", "department": "Pathology",
             "shift": "Night", "contact": "8880004444"},
        ]
        for s in staff:
            saved = data_manager.add_staff(s)
            vector_store.upsert_staff(saved)

    if not data_manager.get_patients():
        patients = [
            {"name": "Ravi Kumar", "age": 34, "gender": "Male", "contact": "7770001111",
             "medical_history": "Hypertension", "allergies": "None", "blood_group": "B+"},
            {"name": "Sneha Gupta", "age": 28, "gender": "Female", "contact": "7770002222",
             "medical_history": "None", "allergies": "Penicillin", "blood_group": "O+"},
            {"name": "Arjun Verma", "age": 45, "gender": "Male", "contact": "7770003333",
             "medical_history": "Type 2 Diabetes", "allergies": "None", "blood_group": "A+"},
            {"name": "Pooja Singh", "age": 30, "gender": "Female", "contact": "7770004444",
             "medical_history": "Asthma", "allergies": "Dust", "blood_group": "AB+"},
            {"name": "Rahul Nair", "age": 52, "gender": "Male", "contact": "7770005555",
             "medical_history": "Coronary artery disease", "allergies": "None", "blood_group": "B-"},
            {"name": "Anjali Desai", "age": 24, "gender": "Female", "contact": "7770006666",
             "medical_history": "None", "allergies": "None", "blood_group": "O-"},
            {"name": "Vikas Malhotra", "age": 60, "gender": "Male", "contact": "7770007777",
             "medical_history": "Arthritis, Hypertension", "allergies": "Aspirin", "blood_group": "A-"},
            {"name": "Neha Kapoor", "age": 19, "gender": "Female", "contact": "7770008888",
             "medical_history": "None", "allergies": "Peanuts", "blood_group": "B+"},
        ]
        for p in patients:
            saved = data_manager.add_patient(p)
            vector_store.upsert_patient(saved)

    if not data_manager.get_medications():
        meds = [
            {"name": "Paracetamol", "description": "Pain reliever and fever reducer",
             "category": "Analgesic", "stock": 100, "reorder_level": 20, "price": 2.5},
            {"name": "Amoxicillin", "description": "Antibiotic for bacterial infections",
             "category": "Antibiotic", "stock": 50, "reorder_level": 15, "price": 5.0},
            {"name": "Ibuprofen", "description": "Anti-inflammatory pain reliever",
             "category": "NSAID", "stock": 8, "reorder_level": 10, "price": 3.0},
            {"name": "Amlodipine", "description": "Used to treat high blood pressure",
             "category": "Antihypertensive", "stock": 40, "reorder_level": 10, "price": 4.2},
            {"name": "Atorvastatin", "description": "Lowers cholesterol, reduces heart disease risk",
             "category": "Statin", "stock": 35, "reorder_level": 10, "price": 6.0},
            {"name": "Metformin", "description": "Used to control blood sugar in type 2 diabetes",
             "category": "Antidiabetic", "stock": 60, "reorder_level": 15, "price": 3.8},
        ]
        for m in meds:
            saved = data_manager.add_medication(m)
            vector_store.upsert_medication(saved)

    # Seed a few appointments so doctor-patient relationships are testable immediately
    if not data_manager.get_appointments():
        doctors = data_manager.get_doctors()
        patients = data_manager.get_patients()

        def find_doc(name_part):
            return next(d for d in doctors if name_part.lower() in d["name"].lower())

        def find_pat(name_part):
            return next(p for p in patients if name_part.lower() in p["name"].lower())

        cardiologist = find_doc("Anita Sharma")
        ortho = find_doc("Rohan Mehta")
        general = find_doc("Suresh Patel")

        ravi = find_pat("Ravi Kumar")
        sneha = find_pat("Sneha Gupta")
        vikas = find_pat("Vikas Malhotra")
        rahul = find_pat("Rahul Nair")

        seed_appointments = [
            {"patient_id": ravi["patient_id"], "doctor_id": cardiologist["doctor_id"],
             "date": "2025-01-10", "time": "10:00", "reason": "Routine BP checkup",
             "status": "completed"},
            {"patient_id": sneha["patient_id"], "doctor_id": cardiologist["doctor_id"],
             "date": "2025-01-15", "time": "11:00", "reason": "Chest discomfort follow-up",
             "status": "completed"},
            {"patient_id": vikas["patient_id"], "doctor_id": ortho["doctor_id"],
             "date": "2025-01-12", "time": "14:00", "reason": "Joint pain evaluation",
             "status": "completed"},
            {"patient_id": rahul["patient_id"], "doctor_id": general["doctor_id"],
             "date": "2025-01-08", "time": "09:00", "reason": "General checkup",
             "status": "completed"},
        ]
        for a in seed_appointments:
            data_manager.add_appointment(a)

    print("✅ Data ready.")
    print("Doctors:", [f"{d['doctor_id']}:{d['name']}" for d in data_manager.get_doctors()])
    print("Staff:", [f"{s['staff_id']}:{s['name']}" for s in data_manager.get_staff()])
    print("Patients:", [f"{p['patient_id']}:{p['name']}" for p in data_manager.get_patients()])
    print("Medications:", [f"{m['med_id']}:{m['name']}" for m in data_manager.get_medications()])
    print("Appointments:", len(data_manager.get_appointments()), "seeded")


if __name__ == "__main__":
    init()