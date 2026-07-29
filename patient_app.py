import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import agents  # already imported, keep it
import data_manager
import vector_store

st.set_page_config(page_title="Patient Portal", page_icon="🧑‍⚕️", layout="wide")

if "vs_initialized" not in st.session_state:
    vector_store.rebuild_all()
    st.session_state.vs_initialized = True

if "patient_agent" not in st.session_state:
    st.session_state.patient_agent = agents.get_patient_agent()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "logged_in_patient" not in st.session_state:
    st.session_state.logged_in_patient = None

st.title("🧑‍⚕️ Patient Portal — Hospital Management System")

with st.sidebar:
    st.header("Login")
    patients = data_manager.get_patients()
    if patients:
        options = {f"{p['name']} (ID {p['patient_id']})": p['patient_id'] for p in patients}
        selected = st.selectbox("Select your profile", ["-- New Patient --"] + list(options.keys()))
        if selected != "-- New Patient --":
            st.session_state.logged_in_patient = options[selected]
        else:
            st.session_state.logged_in_patient = None
            st.info("Chat below to register as a new patient.")
    else:
        st.info("No patients yet. Register via chat!")

    if st.session_state.logged_in_patient:
        patient = data_manager.get_patient(st.session_state.logged_in_patient)
        st.success(f"Logged in as {patient['name']} (ID {patient['patient_id']})")

        st.subheader("📅 My Appointments")
        appts = data_manager.get_appointments_by_patient(patient['patient_id'])
        if appts:
            for a in appts:
                doc = data_manager.get_doctor(a['doctor_id'])
                st.write(f"**{a['date']} {a['time']}** - Dr. {doc['name'] if doc else '?'} ({a['status']})")
        else:
            st.write("No appointments yet.")

        st.subheader("💊 My Prescriptions")
        prescriptions = data_manager.get_prescriptions_by_patient(patient['patient_id'])
        approved = [p for p in prescriptions if p['status'] == 'approved']
        pending_meds = []
        if approved:
            for p in approved:
                st.write(f"**Diagnosis:** {p.get('diagnosis')}")
                for m in p.get('medicines', []):
                    st.write(f"- {m['name']} ({m['dosage']}, {m['frequency']}, {m['duration']}) — *{m['status']}*")
                    if m['status'] != 'taken':
                        pending_meds.append(f"{m['name']} — {m['status']}")
        else:
            st.write("No prescriptions yet.")

        st.subheader("⏰ Medication Reminders")
        if pending_meds:
            for pm in pending_meds:
                st.warning(pm)
        else:
            st.write("No pending medications.")

        st.subheader("📝 Feedback Requests")
        pending_fb = data_manager.get_pending_feedback_requests(patient['patient_id'])
        if pending_fb:
            for fb in pending_fb:
                st.info(fb.get('message', 'Please share feedback about your recent treatment.'))
        else:
            st.write("No pending feedback requests.")

    if st.button("🔄 Refresh Data"):
        vector_store.rebuild_all()
        st.rerun()

st.subheader("💬 Chat with MediBot")
for role, content in st.session_state.chat_history:
    with st.chat_message(role):
        st.write(content)

user_input = st.chat_input("e.g. 'I want to book an appointment with a cardiologist'")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.write(user_input)

    lc_history = []
    for role, content in st.session_state.chat_history[:-1]:
        lc_history.append(HumanMessage(content=content) if role == "user" else AIMessage(content=content))

    context_prefix = ""
    if st.session_state.logged_in_patient:
        context_prefix = f"[Context: Logged in patient_id = {st.session_state.logged_in_patient}] "

    messages = [SystemMessage(content=agents.PATIENT_SYSTEM_PROMPT)] + lc_history + \
               [HumanMessage(content=context_prefix + user_input)]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            st.write(f"DEBUG: Sending to agent: {context_prefix + user_input}")  # TEMP DEBUG
            try:
                result = st.session_state.patient_agent.invoke({"messages": messages})
                answer = result["messages"][-1].content
                st.write(f"DEBUG: Got {len(result['messages'])} messages back")  # TEMP DEBUG
            except Exception as e:
                import traceback
                st.error("An error occurred:")
                st.code(traceback.format_exc())
                answer = f"Sorry, I encountered an error: {e}"
            st.write(answer)

    st.session_state.chat_history.append(("assistant", answer))
    st.rerun()