print("\n--- Testing patient agent ---")
import agents
from langchain_core.messages import HumanMessage, SystemMessage

patient_agent = agents.get_patient_agent()
result = patient_agent.invoke({
    "messages": [
        SystemMessage(content=agents.PATIENT_SYSTEM_PROMPT),
        HumanMessage(content="List all doctors")
    ]
})

print("\n--- FULL MESSAGE TRACE ---")
for i, msg in enumerate(result["messages"]):
    print(f"\n[{i}] Type: {type(msg).__name__}")
    print(f"Content: {msg.content}")
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        print(f"Tool calls: {msg.tool_calls}")
    if hasattr(msg, "name") and msg.name:
        print(f"Tool name: {msg.name}")

print("\n--- FINAL ANSWER ---")
print(result["messages"][-1].content)
print("\n--- Testing tool directly ---")
import tools
direct_result = tools.list_all_doctors.invoke({"speciality": ""})
print("DIRECT TOOL RESULT:", direct_result)