import os
import json

# Replace with your folder path
folder_path = 'responses'

for filename in os.listdir(folder_path):
    if filename.endswith('.json'):
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                print(f"\n--- File: {filename} ---")
                print('Title:', data['example']['meta']['title'])
                print()
                # prompt = data.get("prompt", {})
                # if isinstance(prompt, dict):
                #     # system = prompt.get("system", "")
                #     # user = prompt.get("user", "")
                #     # print(f"System: {system}")
                #     # print(f"User: {user}")
                #     pass
                # else:
                #     print("Prompt is not a dict:", prompt)

                responses = data.get("responses", [])
                print("Responses:")
                for response in responses:
                    print(f"- {response}")

        except Exception as e:
            print(f"Error reading {filename}: {e}")