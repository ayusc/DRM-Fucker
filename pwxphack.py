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
        return

try:
        required_xp = int(sys.argv[1])
except ValueError:
        print("Error: XP value must be a positive integer.")
        return

if required_xp <= 0:
        print("Error: XP value must be greater than 0.")
        return

if required_xp % 100 != 0:
        print("Error: XP value must be a multiple of 100.")
        return

if required_xp > 5000:
        print("Error: maximum allowed value for XP is 5000.")
        return

SESSION_ID = os.environ["SESSION_ID"]
BEARER_TOKEN = os.environ["BEARER_TOKEN"]
CLIENT_ID = os.environ["CLIENT_ID"]

RANDOM_ID = str(uuid.uuid4())

PUBLIC_KEY_PEM = """-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAw5cpnzm8MOaLOmA5BcXO
6B06yYgDAnqGjeNCDYVC/139MvzNtnnEw+3ewBhbMIRfkPKcUHYpuagktEQRVh91
2aoMUwYSE8JbauMsLbmuqYGDkk/rchIaB/Cd0lCODlOJoqtgUjp1qY5w3J+iCZpR
jnazkfr4X/bIASTQRTZEL8reqzLlk1Ko6C+LP+y3SF1cJed2vTXLxm0EgViz6t/j
e+WV9bTka19ZT29fduLyeF8Arj4NtwyowcLDlVkiTSUf5RW5GUYnMtxP4MR3/alm
6FhoJx10WFilRFucTkQscIrKrdtdPpI2YAHNkBsEyvbyx4rxBKdZH+R1fUGgs4Pc
fQIDAQAB
-----END RSA PUBLIC KEY-----"""

rsa_key = RSA.import_key(PUBLIC_KEY_PEM)
cipher_rsa = PKCS1_OAEP.new(rsa_key, hashAlgo=SHA256.new())

raw_aes_key = os.urandom(32)
raw_iv = os.urandom(12)

encrypted_key_bytes = cipher_rsa.encrypt(raw_aes_key)
encrypted_key_b64 = base64.b64encode(encrypted_key_bytes).decode()

SECONDS_PER_XP = 30
SECONDS_TO_ADD = 60

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

    r = requests.post(
        "https://api.penpencil.co/uxncc-be-go/video-stats/v1/sync-stats",
        json=payload,
        headers=headers
    )

    print(r.status_code, r.text)

for i in range(iterations):
    send_chunk(SECONDS_TO_ADD, current_position)
    current_position += SECONDS_TO_ADD
    time.sleep(1.5)

if remaining_seconds > 0:
    send_chunk(remaining_seconds, current_position)
