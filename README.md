# Hospital RAG Multi-Agent Management System

A prototype **Centralized Patient Management System** powered by a multi-agent RAG (Retrieval-Augmented Generation) architecture. Built with **Streamlit**, **LangChain/LangGraph**, **ChromaDB**, and **Groq (Llama models)**.

The system simulates three separate hospital portals — **Patient**, **Doctor**, and **Staff** — each backed by its own conversational AI agent equipped with role-specific tools. All portals share a common JSON data store and a ChromaDB vector store, so actions taken in one portal are reflected across the others in real time.

---

## ✨ Features

- 🤖 **Multi-agent architecture** — separate LangGraph ReAct agents for Patients, Doctors, and Staff, each with its own toolset and system prompt.
- 🔍 **RAG-powered semantic search** over patient, doctor, staff, and medication records using ChromaDB + sentence-transformer embeddings.
- 📅 **Appointment booking** — checks doctor availability and prevents double-booking.
- 🔒 **Access control** — doctors can only view history / suggest / approve prescriptions for patients who actually appear in their own schedule.
- 💊 **Prescription workflow** — AI drafts a suggested prescription based on diagnosis + patient history; doctor reviews, modifies, and approves the final version.
- 📋 **Medication tracking** — tracks each medicine's lifecycle: `assigned → given → taken`, with reminders shown on the patient dashboard.
- 📦 **Smart inventory management** — staff can check stock, flag low-stock items, request orders, and approve them (auto-updates stock).
- 📤 **Real-time data ingestion** — upload new medication or patient records as JSON directly from the Staff portal; the vector DB updates instantly.
- 📝 **Automated feedback / follow-up agent** — drafts and sends a personalized follow-up message to patients after treatment, and logs their feedback + follow-up requests.
- 🕒 **Date/time awareness tool** — agents fetch the real current date/time instead of guessing when users say "today"/"tomorrow".

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Patient Portal  │     │  Doctor Portal   │     │  Staff Portal    │
│ (Streamlit:8501) │     │ (Streamlit:8502) │     │ (Streamlit:8503) │
│                  │     │                  │     │                  │
│  Patient Agent   │     │  Doctor Agent    │     │  Staff Agent     │
│  (LangGraph      │     │  (LangGraph      │     │  (LangGraph      │
│   ReAct + tools) │     │   ReAct + tools) │     │   ReAct + tools) │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                         │
         └────────────┬───────────┴────────────┬────────────┘
                       │                        │
              ┌────────▼────────┐      ┌────────▼────────┐
              │  JSON Data Store │      │    ChromaDB      │
              │  (data/*.json)   │      │  (chroma_db/)     │
              └──────────────────┘      └──────────────────┘
                       │
              ┌────────▼────────┐
              │   Groq API       │
              │  (Llama 3.x)     │
              └──────────────────┘
```

Each Streamlit app is an independent process. They interact through a shared JSON-based data layer (`data_manager.py`) and a shared persistent ChromaDB store (`vector_store.py`). Click **🔄 Refresh Data** in any portal's sidebar to pull the latest changes made from another window.

---

## 📁 Project Structure

```
hospital_rag/
├── requirements.txt
├── .env                   # Your Groq API key (not committed)
├── config.py              # Paths & environment config
├── data_manager.py        # CRUD operations on JSON "database"
├── vector_store.py        # ChromaDB embedding & semantic search
├── sub_agents.py          # Prescription-suggestion & feedback-drafting LLM chains
├── tools.py                # All LangChain tools used by the 3 agents
├── agents.py               # LangGraph ReAct agent builders + system prompts
├── init_data.py            # Seeds sample doctors/patients/staff/medications
├── patient_app.py          # Streamlit app — Patient Portal
├── doctor_app.py           # Streamlit app — Doctor Portal
├── staff_app.py            # Streamlit app — Staff Portal
├── test_agent.py           # Standalone debug script for testing LLM/agent/tools
├── data/                   # Auto-generated JSON data files
└── chroma_db/              # Auto-generated persistent vector store
```

---

## 🧰 Tech Stack

| Component        | Technology                                      |
|-------------------|--------------------------------------------------|
| UI                | Streamlit                                        |
| LLM               | Groq API (Llama 3.x, e.g. `llama-3.3-70b-versatile`) |
| Agent framework   | LangGraph (`create_react_agent`) + LangChain Core |
| Vector DB         | ChromaDB (persistent, local)                     |
| Embeddings        | `sentence-transformers` (`all-MiniLM-L6-v2`)     |
| Data storage      | JSON files (lightweight, no external DB needed)  |

---

## ⚙️ Prerequisites

- Python 3.10+
- A free [Groq API key](https://console.groq.com/keys)

---

## 🚀 Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/hospital-rag-multiagent.git
cd hospital-rag-multiagent
```

### 2. Create and activate a virtual environment

> ⚠️ Strongly recommended — avoids dependency conflicts with any globally installed LangChain versions.

```bash
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

> 💡 `llama-3.3-70b-versatile` is recommended for reliable multi-step tool calling. Smaller models (e.g. `llama-3.1-8b-instant`) are faster but may occasionally fail on chained tool calls (e.g., check-availability → book).

### 5. Seed the database

This populates sample doctors, patients, staff, medications, and a few pre-linked appointments, and builds the initial ChromaDB embeddings.

```bash
python init_data.py
```

### 6. (Optional) Sanity-check the agent pipeline

```bash
python test_agent.py
```

You should see a real LLM response and, further down, a full message trace showing a tool call + tool result for `list_all_doctors`.

---

## ▶️ Running the App

Run each portal in its **own terminal window** (all with the venv activated):

```bash
streamlit run patient_app.py --server.port 8501
```

```bash
streamlit run doctor_app.py --server.port 8502
```

```bash
streamlit run staff_app.py --server.port 8503
```

Then open in your browser:

| Portal   | URL                          |
|----------|-------------------------------|
| Patient  | http://localhost:8501         |
| Doctor   | http://localhost:8502         |
| Staff    | http://localhost:8503         |

---

## 🧪 Demo Walkthrough

1. **Patient** logs in (or registers as new) and chats:
   > "I want to book an appointment with a cardiologist tomorrow at 10am"

   The agent fetches the real date, checks the doctor's availability, and books the slot.

2. **Doctor** (e.g. Dr. Anita Sharma) logs in, sees the new appointment in the sidebar, and chats:
   > "Patient 2 mentioned heart pain and high blood pressure, suggest a prescription"

   The AI drafts a suggested prescription. The doctor reviews/edits it, then says:
   > "Approve this prescription: Amlodipine 5mg once daily for 30 days, Atorvastatin 10mg once daily for 30 days"

3. **Patient** clicks 🔄 Refresh and sees the new prescription on their dashboard, with medicine status "assigned".

4. **Staff** logs in and chats:
   > "Mark Amlodipine as given for prescription 1"

   Inventory stock automatically decrements.

5. **Patient** marks the medicine as "taken" via chat once they've had it.

6. **Staff** (or Doctor) sends a follow-up:
   > "Send a feedback request to patient 2 about their cardiology treatment"

   This appears as a pending feedback request in the Patient portal's sidebar.

7. **Staff** uploads a new medication or patient batch via JSON file upload in the sidebar — instantly embedded into ChromaDB, available to all agents in real time.

---

## 🔐 Access Control

Doctors can only access medical history, suggest prescriptions, or approve prescriptions for **patients who already have an appointment with them** (past or scheduled). Attempting to access an unrelated patient's data returns an explicit "Access denied" response instead of leaking information.

---

## 🗂️ Data Model

All data lives as JSON files under `data/`, auto-created on first run:

| File                   | Description                                      |
|------------------------|---------------------------------------------------|
| `patients.json`        | Patient demographics, history, allergies          |
| `doctors.json`         | Doctor specialities, department, availability     |
| `staff.json`           | Staff roles, department, shift                    |
| `medications.json`     | Medicine name, description, stock, reorder level  |
| `appointments.json`    | Patient–doctor bookings with date/time/status     |
| `prescriptions.json`   | Approved prescriptions with per-medicine status   |
| `feedback.json`        | Patient feedback & follow-up requests             |
| `med_orders.json`      | Medication restock requests & approvals           |

You can inspect/edit these directly for debugging, or use the provided JSON upload feature in the Staff portal.

---

## 🧯 Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: langchain_core.memory` | Conflicting `langchain` / `langchain-core` versions | Use a clean venv and install exact pinned versions from `requirements.txt` |
| `KeyError: '_type'` on ChromaDB collection creation | Corrupted / incompatible `chroma_db/` folder from a previous version | `rm -rf chroma_db && python init_data.py` |
| `Failed to send telemetry event ... capture()` warnings | Known ChromaDB + posthog version mismatch | Harmless — can be ignored, or pin `posthog<3.0.0` |
| `tool_use_failed` / malformed function call errors | Small models (e.g. 8B) can produce invalid tool-call syntax on complex multi-step tasks | Switch to `llama-3.3-70b-versatile` in `.env`, set `temperature=0` |
| `tool call validation failed: expected integer, but got string` | Groq occasionally sends numeric IDs as strings | Already handled — tool signatures accept `Union[int, str]` and coerce internally |
| No response in browser chat, no visible error | Silent exception swallowed | Check the terminal running `streamlit run ...` for tracebacks; the apps also render `st.exception()` on failure |

For deeper debugging, use `test_agent.py` to test the Groq connection and agent tool-calling pipeline outside of Streamlit.

---

## 🛣️ Roadmap / Possible Extensions

- [ ] Persistent per-user login (currently a simple dropdown "select your profile" simulates login)
- [ ] Replace JSON storage with a real database (SQLite/Postgres) for concurrency safety
- [ ] Streaming responses in the chat UI
- [ ] Role-based dashboards with charts (appointment load, inventory trends)
- [ ] Automated background job for feedback agent (currently triggered manually by staff/doctor)
- [ ] Voice input/output for accessibility

---

## ⚠️ Disclaimer

This is a **prototype/demo project** for educational and illustrative purposes only. AI-suggested prescriptions are **not medical advice** and must always be reviewed and approved by a qualified doctor before use. Do not use this system with real patient data or in a production clinical setting without proper security, compliance (e.g. HIPAA), and validation measures.

---

## 📄 License

MIT License — free to use, modify, and build upon.
