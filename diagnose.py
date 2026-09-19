#!/usr/bin/env python3
"""
Diagnostic utility to test your Gemini API Key and discover exact working model IDs.
Run with: python diagnose.py
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY", "").strip().strip("'").strip('"')

print("=" * 60)
print("   JARVIS MOBILE // GEMINI API KEY & MODEL DIAGNOSTIC")
print("=" * 60)

if not api_key or api_key == "your_gemini_api_key_here":
    print("\n[ERROR] GEMINI_API_KEY is not set or still default in .env!")
    print("Please edit .env and paste your key from https://aistudio.google.com/")
    sys.exit(1)

masked_key = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
print(f"[*] Testing API Key: {masked_key}")

# 1. Query ListModels API
print("\n[*] Step 1: Querying Google Generative Language ListModels API...")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
headers = {"x-goog-api-key": api_key}

try:
    res = requests.get(url, headers=headers, timeout=12)
    print(f"[*] HTTP Status: {res.status_code}")
    if res.status_code != 200:
        print(f"[!] Google API Error response:\n{res.text}")
        print("\nPlease check that your API key is valid and enabled in Google AI Studio.")
        sys.exit(1)

    data = res.json()
    all_models = data.get("models", [])
    print(f"[✓] Successfully retrieved {len(all_models)} models from Google!")

    # Filter models that support generateContent
    usable_models = []
    for m in all_models:
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" in methods or "bidiGenerateContent" in methods:
            name = m.get("name", "").replace("models/", "")
            usable_models.append(name)

    print("\n[*] Step 2: Available Models for Content Generation:")
    for idx, name in enumerate(usable_models, 1):
        print(f"    {idx}. {name}")

    if not usable_models:
        print("[!] No generateContent models found for this key.")
        sys.exit(1)

    # Step 3: Test generateContent with candidate models
    print("\n[*] Step 3: Testing live generation with top candidates...")
    working_model = None

    # Prioritize flash / live models
    test_queue = sorted(usable_models, key=lambda x: (
        0 if "flash" in x.lower() else 1,
        0 if "3" in x else 1,
        0 if "2" in x else 1
    ))

    for model_id in test_queue[:6]:
        print(f"    Testing model: '{model_id}'...", end=" ", flush=True)
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
        test_payload = {
            "contents": [{"parts": [{"text": "Say 'JARVIS online' in 3 words."}]}]
        }
        try:
            r = requests.post(gen_url, headers={"Content-Type": "application/json", "x-goog-api-key": api_key}, json=test_payload, timeout=15)
            if r.status_code == 200:
                resp_json = r.json()
                reply = resp_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                print(f"[SUCCESS!]\n       Response: \"{reply}\"")
                working_model = model_id
                break
            else:
                print(f"[FAILED: {r.status_code} - {r.json().get('error', {}).get('message', r.text[:60])}]")
        except Exception as e:
            print(f"[ERROR: {e}]")

    if working_model:
        print("\n" + "=" * 60)
        print(f"[✓] WINNER: Model '{working_model}' is 100% operational!")
        print("=" * 60)

        # Update .env with the working model
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
            
            new_lines = []
            found_model = False
            for line in lines:
                if line.startswith("GEMINI_MODEL="):
                    new_lines.append(f"GEMINI_MODEL={working_model}\n")
                    found_model = True
                else:
                    new_lines.append(line)
            if not found_model:
                new_lines.append(f"GEMINI_MODEL={working_model}\n")

            with open(env_path, "w") as f:
                f.writelines(new_lines)
            print(f"[+] Saved GEMINI_MODEL={working_model} to your .env file!")
            print("\nYou can now start Jarvis: python main.py")
    else:
        print("\n[!] None of the tested models responded successfully. Please verify quota or permissions.")

except Exception as e:
    print(f"\n[!] Network or request error: {e}")
