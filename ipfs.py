import requests
import json

PINATA_API_KEY = "1cc2d8534ac2f4903d17"
PINATA_SECRET_API_KEY = "49ac132f684bc8427e1b920bbda8b743251733e9e9732bec7267ae83ec49ae51"

PINATA_PIN_JSON_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
PINATA_GATEWAY = "https://gateway.pinata.cloud/ipfs/"

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
	#YOUR CODE HERE
	headers = {
        "Content-Type": "application/json",
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_API_KEY
    }

    payload = {
        "pinataContent": data
    }

    response = requests.post(PINATA_PIN_JSON_URL, headers=headers, json=payload)
    response.raise_for_status()

    cid = response.json()["IpfsHash"]
    return cid

def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	#YOUR CODE HERE
	url = f"{PINATA_GATEWAY}{cid}"
    response = requests.get(url)
    response.raise_for_status()

    if content_type == "json":
        data = response.json()
    else:
        raise ValueError("Unsupported content type. Only 'json' is supported.")

	assert isinstance(data,dict), f"get_from_ipfs should return a dict"
	return data
