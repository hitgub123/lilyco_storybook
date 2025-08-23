import json
     
        # --- 请确保这里的路径是正确的 ---
data_file_path = "data/training_data_for_agent.jsonl"
    
try:
    with open(data_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("--- SUCCESS! The file is a valid JSON. ---")
    print(f"Loaded {len(data)} records.")
except json.JSONDecodeError as e:
    print("--- FAILED: The file is NOT a valid JSON. ---")
    print(f"Error details: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")