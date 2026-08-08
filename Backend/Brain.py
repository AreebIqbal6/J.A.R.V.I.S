import requests
import os
from dotenv import dotenv_values

# Load Keys and Variables dynamically
env_vars = dotenv_values(".env")
HuggingFaceAPIKey = env_vars.get("HuggingFaceAPIKey")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "J.A.R.V.I.S")

def Qna(query):
    """
    The Brain: Sends text to a powerful LLM via Hugging Face with fast failover.
    """
    models = [
        "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
        "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta",
        "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"
    ]
    
    # Dynamically inject the user and assistant names
    system_prompt = (
        f"You are {Assistantname}, an advanced AI assistant tailored for {Username}. "
        "You are witty, concise, and highly intelligent. "
        "Your goal is to assist with tasks, answer questions, and provide insights. "
        "Keep your answers short and to the point unless asked for details. "
        "Address the user respectfully as 'sir'."
    )
    
    formatted_prompt = f"<s>[INST] {system_prompt} \n\nQuery: {query} [/INST]"

    headers = {"Authorization": f"Bearer {HuggingFaceAPIKey}"}
    
    payload = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True,
            "return_full_text": False 
        }
    }

    # Fast Failover Loop
    for model_url in models:
        try:
            # 5-second timeout prevents the GUI from freezing if a model is down
            response = requests.post(model_url, headers=headers, json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                
                if isinstance(result, list) and 'generated_text' in result[0]:
                    return result[0]['generated_text'].strip()
                elif isinstance(result, dict) and 'generated_text' in result:
                    return result['generated_text'].strip()
        except Exception:
            # Silently skip to the next backup model on timeout or error
            continue

    return "My cognitive systems are offline. Please check your connection, sir."

# Test it locally
if __name__ == "__main__":
    print(Qna("Who are you?"))