import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import agents
import data_manager
import vector_store

st.set_page_config(page_title="Doctor Portal", page_icon="🩺", layout="wide")

if "vs_initialized" not in st.session_state:
    vector_store.rebuild_all()
    st.session_state.vs_initialized = True

if "doctor_agent" not in st.session_state:
    st.session_state.doctor_agent = agents.get_doctor_agent()
if "doc_chat_history" not in st.session_state:
    st.session_state.doc_chat_history = []
if "logged_in_doctor" not in st.session_state:
    st.session_state.logged_in_doctor = None

st.title("🩺 Doctor Portal — Hospital Management System")

with st.sidebar:
    st.header("Login")
    doctors = data_manager.get_doctors()
    if doctors:
        options = {f"Dr. {d['name']} (ID {d['doctor_id']})": d['doctor_id'] for d in doctors}
        selected = st.selectbox("Select your profile", list(options.keys()))
        st.session_state.logged_in_doctor = options[selected]

    if st.session_state.logged_in_doctor:
        doctor = data_manager.get_doctor(st.session_state.logged_in_doctor)
        st.success(f"Logged in as Dr. {doctor['name']}")
        st.write(f"**Speciality:** {doctor['speciality']}")
        st.write(f"**Department:** {doctor['department']}")

        st.subheader("📅 My Appointments")
        appts = data_manager.get_appointments_by_doctor(doctor['doctor_id'])
        if appts:
            for a in appts:
                patient = data_manager.get_patient(a['patient_id'])
                st.write(f"**{a['date']} {a['time']}** - {patient['name'] if patient else '?'} "
                         f"({a['status']}) - {a.get('reason','')}")
        else:
            st.write("No appointments yet.")

    if st.button("🔄 Refresh Data"):
        vector_store.rebuild_all()
        st.rerun()
st.subheader("💬 Chat with MediBot (Doctor Assistant)")
for role, content in st.session_state.doc_chat_history:
    with st.chat_message(role):
        st.write(content)

user_input = st.chat_input("e.g. 'Show my schedule' or 'Suggest a prescription for patient 1 with fever'")

if user_input:
    st.session_state.doc_chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.write(user_input)

    lc_history = []
    for role, content in st.session_state.doc_chat_history[:-1]:
        lc_history.append(HumanMessage(content=content) if role == "user" else AIMessage(content=content))

    context_prefix = ""
    if st.session_state.logged_in_doctor:
        context_prefix = f"[Context: Logged in doctor_id = {st.session_state.logged_in_doctor}] "

    messages = [SystemMessage(content=agents.DOCTOR_SYSTEM_PROMPT)] + lc_history + \
               [HumanMessage(content=context_prefix + user_input)]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = st.session_state.doctor_agent.invoke({"messages": messages})
                answer = result["messages"][-1].content
            except Exception as e:
                answer = f"Sorry, I encountered an error: {e}"
            st.write(answer)

    st.session_state.doc_chat_history.append(("assistant", answer))
    st.rerun()