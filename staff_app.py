import streamlit as st
import json
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import agents
import data_manager
import vector_store

st.set_page_config(page_title="Staff Portal", page_icon="🧑‍💼", layout="wide")

if "vs_initialized" not in st.session_state:
    vector_store.rebuild_all()
    st.session_state.vs_initialized = True

if "staff_agent" not in st.session_state:
    st.session_state.staff_agent = agents.get_staff_agent()
if "staff_chat_history" not in st.session_state:
    st.session_state.staff_chat_history = []
if "logged_in_staff" not in st.session_state:
    st.session_state.logged_in_staff = None

st.title("🧑‍💼 Staff Portal — Hospital Management System")

with st.sidebar:
    st.header("Login")
    staff_list = data_manager.get_staff()
    if staff_list:
        options = {f"{s['name']} (ID {s['staff_id']})": s['staff_id'] for s in staff_list}
        selected = st.selectbox("Select your profile", list(options.keys()))
        st.session_state.logged_in_staff = options[selected]

    if st.session_state.logged_in_staff:
        staff = data_manager.get_staff_member(st.session_state.logged_in_staff)
        st.success(f"Logged in as {staff['name']} ({staff['role']})")

    st.subheader("💊 Inventory Snapshot")
    for m in data_manager.get_medications():
        flag = "⚠️ LOW" if m.get("stock", 0) <= m.get("reorder_level", 0) else "✅"
        st.write(f"{flag} {m['name']}: {m['stock']} units")

    st.subheader("📦 Pending Orders")
    orders = [o for o in data_manager.get_med_orders() if o['status'] == 'pending_approval']
    if orders:
        for o in orders:
            st.write(f"Order {o['order_id']}: {o['quantity']}x {o['med_name']}")
    else:
        st.write("No pending orders.")

    st.divider()
    st.subheader("📤 Upload New Medication JSON")
    med_file = st.file_uploader("Single object or list of medications", type="json", key="med_upload")
    if med_file is not None:
        try:
            content = json.load(med_file)
            items = content if isinstance(content, list) else [content]
            for item in items:
                saved = data_manager.add_medication(item)
                vector_store.upsert_medication(saved)
            st.success(f"Added {len(items)} medication(s).")
        except Exception as e:
            st.error(f"Error: {e}")

    st.subheader("📤 Upload Patient JSON")
    patient_file = st.file_uploader("Single object or list of patients", type="json", key="patient_upload")
    if patient_file is not None:
        try:
            content = json.load(patient_file)
            items = content if isinstance(content, list) else [content]
            for item in items:
                saved = data_manager.add_patient(item)
                vector_store.upsert_patient(saved)
            st.success(f"Added {len(items)} patient(s).")
        except Exception as e:
            st.error(f"Error: {e}")

    if st.button("🔄 Refresh Data"):
        vector_store.rebuild_all()
        st.rerun()
st.subheader("💬 Chat with MediBot (Staff Assistant)")
for role, content in st.session_state.staff_chat_history:
    with st.chat_message(role):
        st.write(content)

user_input = st.chat_input("e.g. 'Show inventory status' or 'Approve order 1'")

if user_input:
    st.session_state.staff_chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.write(user_input)

    lc_history = []
    for role, content in st.session_state.staff_chat_history[:-1]:
        lc_history.append(HumanMessage(content=content) if role == "user" else AIMessage(content=content))

    context_prefix = ""
    if st.session_state.logged_in_staff:
        context_prefix = f"[Context: Logged in staff_id = {st.session_state.logged_in_staff}] "

    messages = [SystemMessage(content=agents.STAFF_SYSTEM_PROMPT)] + lc_history + \
               [HumanMessage(content=context_prefix + user_input)]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = st.session_state.staff_agent.invoke({"messages": messages})
                answer = result["messages"][-1].content
            except Exception as e:
                answer = f"Sorry, I encountered an error: {e}"
            st.write(answer)

    st.session_state.staff_chat_history.append(("assistant", answer))
    st.rerun()