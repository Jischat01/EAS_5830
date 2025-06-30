import requests
import json

API_KEY = "a27b8cfa61230e73a7c6"
SECRET_API_KEY = "e0c12d7dccc3abe3282a5a9a9c08067089849aab53ff3006b30304b068628cfb"

PINATA_PIN_JSON_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
PINATA_GATEWAY = "https://gateway.pinata.cloud/ipfs/"

def pin_to_ipfs(data):
    assert isinstance(data, dict), f"Error pin_to_ipfs expects a dictionary"

    headers = {
        "Content-Type": "application/json",
        "pinata_api_key": API_KEY,
        "pinata_secret_api_key": SECRET_API_KEY
    }

    payload = {
        "pinataContent": data
    }

    response = requests.post(PINATA_PIN_JSON_URL, headers=headers, json=payload)
    response.raise_for_status()

    cid = response.json()["IpfsHash"]
    return cid

def get_from_ipfs(cid, content_type="json"):
    assert isinstance(cid, str), f"get_from_ipfs accepts a cid in the form of a string"

    url = f"{PINATA_GATEWAY}{cid}"
    response = requests.get(url)
    response.raise_for_status()

    if content_type == "json":
        data = response.json()
    else:
        raise ValueError("Unsupported content type. Only 'json' is supported.")

    assert isinstance(data, dict), f"get_from_ipfs should return a dict"
    return data
