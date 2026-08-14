from langchain_core.messages import HumanMessage
from smart_money_tracker.agents.graph import build_tracker_graph
import uuid

graph = build_tracker_graph()
current_thread_id = uuid.uuid4()
print("=== Smart Money Tracker (Ketik 'exit' untuk keluar) ===")

while True:
    user_prompt = input("\nMasukkan prompt: ")
    if user_prompt.lower() == "exit":
        break
    
    config = {"configurable": {"thread_id": current_thread_id}}

    input_data = {
        "messages": [HumanMessage(content=user_prompt)],
        "user_id": "usr_telegram_123",
        "channel": "telegram",
        "ref_date": "2026-08-14"
    }

    output = graph.invoke(input_data, config=config)
    
    print(f"\nBot [{output.get('status')}]:\n{output.get('final_message')}")

    if output.get("status") == "success":
        current_thread_id = str(uuid.uuid4())
        

    