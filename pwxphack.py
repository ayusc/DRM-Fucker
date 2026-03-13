# A HACK FOR NOTORIOUSLY GAINING XP's (CREDITS) IN PHYSICS WALLAH WITHOUT DOING ANYTHING
# WARNING: USE AT YOUR OWN RISK !! 
# USE YOUR OWN CREDENTIALS 

import os
import json
import base64
import requests
import time
import uuid
import sys
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256

if len(sys.argv) != 2:
        print("Error: XP value must be provided.")
        print("Usage: python script.py <value>")
        sys.exit(0)

try:
        required_xp = int(sys.argv[1])
except ValueError:
        print("Error: XP value must be a positive integer.")
        sys.exit(0)

if required_xp <= 0:
        print("Error: XP value must be greater than 0.")
        sys.exit(0)

if required_xp % 100 != 0:
        print("Error: XP value must be a multiple of 100.")
        sys.exit(0)

if required_xp > 5000:
        print("Error: maximum allowed value for XP is 5000.")
        sys.exit(0)

SESSION_ID = os.environ["SESSION_ID"]
BEARER_TOKEN = os.environ["BEARER_TOKEN"]
CLIENT_ID = os.environ["CLIENT_ID"]
PUBLIC_KEY_PEM = os.environ["PUBLIC_KEY_PEM"].replace("\\n", "\n")
RANDOM_ID = str(uuid.uuid4())

rsa_key = RSA.import_key(PUBLIC_KEY_PEM)
cipher_rsa = PKCS1_OAEP.new(rsa_key, hashAlgo=SHA256.new())

raw_aes_key = os.urandom(32)
raw_iv = os.urandom(12)

encrypted_key_bytes = cipher_rsa.encrypt(raw_aes_key)
encrypted_key_b64 = base64.b64encode(encrypted_key_bytes).decode()

SECONDS_PER_XP = 30
SECONDS_TO_ADD = 60
all_success = True

total_watch_seconds = required_xp * SECONDS_PER_XP
iterations = total_watch_seconds // SECONDS_TO_ADD
remaining_seconds = total_watch_seconds % SECONDS_TO_ADD

current_position = 61

headers = {
    "authorization": f"Bearer {BEARER_TOKEN}",
    "content-type": "application/json",
    "client-type": "WEB",
    "client-id": CLIENT_ID,
    "client-version": "200",
    "version": "0.0.1",
    "randomid": RANDOM_ID
}

def send_chunk(duration, position):
    fake_stats = {
        "id": SESSION_ID,
        "eType": "stream_sync",
        "seekAt": position,
        "exitAt": position + duration,
        "start": int(time.time() * 1000),
        "duration": duration,
        "quality": "Auto",
        "isAudio": False,
        "len": 6608
    }

    plaintext_bytes = json.dumps(fake_stats, separators=(',', ':')).encode()

    cipher_aes = AES.new(raw_aes_key, AES.MODE_GCM, nonce=raw_iv)
    ciphertext, tag = cipher_aes.encrypt_and_digest(plaintext_bytes)

    encrypted_data_bytes = ciphertext + tag
    encrypted_data_b64 = base64.b64encode(encrypted_data_bytes).decode()
    iv_b64 = base64.b64encode(raw_iv).decode()

    payload = {
        "encryptedKey": encrypted_key_b64,
        "encryptedData": encrypted_data_b64,
        "iv": iv_b64,
        "id": SESSION_ID
    }

    response = requests.post(
    "https://api.penpencil.co/uxncc-be-go/video-stats/v1/sync-stats",
    json=payload,
    headers=headers
    )

    try:
      data = response.json()
    except:
      data = {}

    if response.status_code == 200 and data.get("message") == "Stats synced successfully":
       print(f"Sending chunks ({i+1}/{iterations}) of credits - 2XP", flush=True)
    else:
       all_success = False
       print(f"\nRequest failed: {response.status_code} {response.text}")

for i in range(iterations):
    send_chunk(SECONDS_TO_ADD, current_position)
    current_position += SECONDS_TO_ADD
    time.sleep(1)

if remaining_seconds > 0:
    send_chunk(remaining_seconds, current_position)
    
if all_success:
    print(f"\nSuccessfully Credited {required_xp}XP to your account ✅")
else:
    print("\nProcess completed but some chunks failed.")
