import os
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

ZEN_API_KEY = os.getenv("ZEN_API_KEY")

if not ZEN_API_KEY:
    print("Warning: ZEN_API_KEY not found in .env")


ENDPOINTS = {
    "chat": "/v1/chat/completions",
    "responses": "/v1/responses",
    "messages": "/v1/messages",
    "google": "/v1/models/{}",
}

MODEL_CONFIGS = {
    # OpenAI-compatible (/v1/chat/completions)
    "kimi-k2.5": "chat",
    "kimi-k2.5-free": "chat",
    "kimi-k2-thinking": "chat",
    "kimi-k2": "chat",
    "glm-4.7": "chat",
    "glm-4.7-free": "chat",
    "glm-4.6": "chat",
    "minimax-m2.1": "chat",    
    "qwen3-coder": "chat",
    "big-pickle": "chat",
    # Responses API (/v1/responses)
    "gpt-5.2": "responses",
    "gpt-5.2-codex": "responses",
    "gpt-5.1": "responses",
    "gpt-5.1-codex": "responses",
    "gpt-5.1-codex-max": "responses",
    "gpt-5.1-codex-mini": "responses",
    "gpt-5": "responses",
    "gpt-5-codex": "responses",
    "gpt-5-nano": "responses",
    # Anthropic messages API (/v1/messages)
    "claude-sonnet-4-5": "messages",
    "claude-sonnet-4-6": "messages",
    "claude-sonnet-4": "messages",
    "claude-haiku-4-5": "messages",
    "claude-3-5-haiku": "messages",
    "claude-opus-4-6": "messages",
    "claude-opus-4-5": "messages",
    "claude-opus-4-1": "messages",
    "minimax-m2.1-free": "chat",
    # Google models (/v1/models/{model})
    "gemini-3-pro": "google",
    "gemini-3-flash": "google",
}

BASE_URL = "https://opencode.ai/zen"

def get_endpoint(model):
    endpoint_type = MODEL_CONFIGS.get(model, "chat")
    if endpoint_type == "google":
        return ENDPOINTS["google"].format(model)
    return ENDPOINTS[endpoint_type]

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
    headers = {"Authorization": f"Bearer {ZEN_API_KEY}"}
    
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
                endpoint_type = MODEL_CONFIGS.get(mid, "chat")
                print(f"  {mid:30} | {endpoint_type:12} | {name}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def chat(prompt, model):
    endpoint_type = MODEL_CONFIGS.get(model, "chat")
    endpoint = get_endpoint(model)
    url = f"{BASE_URL}{endpoint}"

    
    headers = {
        "Authorization": f"Bearer {ZEN_API_KEY}",
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
    parser = argparse.ArgumentParser(description="Test OpenCode Zen API")
    parser.add_argument("--models", action="store_true", help="Listar modelos disponibles")
    parser.add_argument("--model", default="kimi-k2.5-free", help="Modelo a usar")
    parser.add_argument("prompt", nargs="?", help="Prompt para enviar al modelo")
    
    args = parser.parse_args()
    
    if args.models:
        list_models()
    elif args.prompt:
        chat(args.prompt, args.model)
    else:
        parser.print_help()
