import os
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY not found in .env")


ENDPOINTS = {
    "chat": "/v1/chat/completions",
    "responses": "/v1/responses",
    "messages": "/v1/messages",
    "google": "/v1/models/{}",
}


BASE_URL = "https://openrouter.ai/api"

def get_endpoint(model):
    return ENDPOINTS["chat"]

def build_payload(model, prompt, endpoint_type):
    if endpoint_type == "responses":
        return {
            "model": model,
            "input": prompt
        }
    elif endpoint_type == "messages":
        return {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
    else:  # chat
        return {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }

def extract_content(response, endpoint_type):
    data = response.json()
    
    if endpoint_type == "responses":
        return data.get("output", [{}])[0].get("content", [{}])[0].get("text", "")
    elif endpoint_type == "messages":
        return data.get("content", [{}])[0].get("text", "")
    else:  # chat
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

def list_models():
    url = f"{BASE_URL}/v1/models"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            print(f"Modelos disponibles ({len(models)}):")
            print("-" * 60)
            for m in models:
                mid = m.get("id", "")
                name = m.get("name", "")
                endpoint_type = "chat"
                print(f"  {mid:60} | {endpoint_type:12} | {name}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def chat(prompt, model):
    endpoint_type = "chat"
    endpoint = get_endpoint(model)
    url = f"{BASE_URL}{endpoint}"

    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = build_payload(model, prompt, endpoint_type)
    
    print(f"Modelo: {model}")
    print(f"Endpoint: {endpoint}")
    print("-" * 40)
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            content = extract_content(response, endpoint_type)
            print(content)
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test OpenRouter API")
    parser.add_argument("--models", action="store_true", help="Listar modelos disponibles")
    parser.add_argument("--model", default="openrouter/free", help="Modelo a usar")
    parser.add_argument("prompt", nargs="?", help="Prompt para enviar al modelo")
    
    args = parser.parse_args()
    
    if args.models:
        list_models()
    elif args.prompt:
        chat(args.prompt, args.model)
    else:
        parser.print_help()
