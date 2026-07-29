from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import config

llm = ChatGroq(groq_api_key=config.GROQ_API_KEY, model_name=config.GROQ_MODEL, temperature=0.3)

# ---------------- Prescription Suggestion Agent ----------------
prescription_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a clinical assistant AI helping doctors draft prescriptions. "
               "Based on the diagnosis/symptoms and patient history given, suggest a prescription. "
               "This is only a SUGGESTION for doctor review, never final. "
               "Return a clear list of medicines with dosage, frequency and duration, plus general advice. "
               "Keep it concise."),
    ("human", "Patient history: {history}\n\nSymptoms/Diagnosis: {diagnosis}\n\nSuggest a prescription.")
])
prescription_chain = prescription_prompt | llm


def suggest_prescription(diagnosis, history="None"):
    result = prescription_chain.invoke({"diagnosis": diagnosis, "history": history})
    return result.content


# ---------------- Feedback / Follow-up Agent ----------------
feedback_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a caring hospital follow-up assistant. Write a short, warm message "
               "to a patient asking about their recovery after treatment and whether they need "
               "a follow-up appointment. Keep it under 60 words."),
    ("human", "Patient name: {name}\nTreatment/diagnosis: {treatment}")
])
feedback_chain = feedback_prompt | llm


def draft_feedback_message(name, treatment):
    result = feedback_chain.invoke({"name": name, "treatment": treatment})
    return result.content