from web3 import Web3
import json

# --- Connect to Avalanche Fuji Testnet ---
w3 = Web3(Web3.HTTPProvider("https://api.avax-test.network/ext/bc/C/rpc"))

# --- Wallet Setup ---
private_key = "0xffd0400eb44cbd37bb105f9284dae8d7a85c840d9ac359b9b0baf8cfa3b72ac9"  # Replace with your private key (keep safe)
account = w3.eth.account.from_key(private_key)
address = account.address
print(f"Wallet address: {address}")

# --- Check AVAX Balance ---
balance = w3.eth.get_balance(address)
avax_balance = w3.from_wei(balance, "ether")
print(f"AVAX Balance: {avax_balance} AVAX")

if balance == 0:
    print("You have 0 AVAX. Please request testnet funds before minting.")
    exit()

# --- Load Contract ABI ---
with open("NFT.abi", "r") as abi_file:
    abi = json.load(abi_file)

# --- Contract Setup ---
contract_address = "0x85ac2e065d4526FBeE6a2253389669a12318A412"
contract = w3.eth.contract(address=contract_address, abi=abi)

# --- Prepare nonce in bytes32 format ---
int_nonce = 44
bytes_nonce = int_nonce.to_bytes(32, byteorder="big")

# --- Build transaction ---
nonce = w3.eth.get_transaction_count(address)
print(f"Minting NFT with claim({address}, {bytes_nonce.hex()})...")

txn = contract.functions.claim(address, bytes_nonce).build_transaction({
    "from": address,
    "gas": 300000,
    "gasPrice": w3.to_wei("25", "gwei"),
    "nonce": nonce,
    "chainId": 43113  # Fuji Testnet
})

# --- Sign and Send ---
signed_txn = w3.eth.account.sign_transaction(txn, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
print(f"Transaction sent! Hash: {tx_hash.hex()}")

# --- Wait for Confirmation ---
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

if receipt.status == 1:
    print("NFT minted successfully!")
else:
    print("Transaction failed.")
