from web3 import Web3
import json

# --- Inline fallback for construct_poa_middleware ---
def construct_poa_middleware():
    def middleware(make_request, w3):
        def middleware_fn(method, params):
            if method in ("eth_getBlockByNumber", "eth_getBlockByHash"):
                response = make_request(method, params)
                if "result" in response and isinstance(response["result"], dict):
                    response["result"].pop("extraData", None)
                return response
            return make_request(method, params)
        return middleware_fn
    return middleware

# --- Connect to Avalanche Fuji Testnet ---
w3 = Web3(Web3.HTTPProvider("https://api.avax-test.network/ext/bc/C/rpc"))
w3.middleware_onion.inject(construct_poa_middleware(), layer=0)

# --- Wallet Setup ---
private_key = "0xffd0400eb44cbd37bb105f9284dae8d7a85c840d9ac359b9b0baf8cfa3b72ac9"  # 🔐 Replace with your private key (keep it safe)
account = w3.eth.account.privateKeyToAccount(private_key)
address = account.address
print(f"Wallet address: {address}")

# --- Check AVAX Balance ---
balance = w3.eth.getBalance(address)
avax_balance = w3.fromWei(balance, "ether")
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

# --- Prepare a fixed nonce and convert to bytes32 ---
int_nonce = 39
bytes_nonce = int_nonce.to_bytes(32, byteorder="big")  # Proper bytes32 format

# --- Build transaction ---
nonce = w3.eth.getTransactionCount(address)
print(f"Minting NFT with claim({address}, {bytes_nonce.hex()})...")

txn = contract.functions.claim(address, bytes_nonce).buildTransaction({
    "from": address,
    "gas": 300000,
    "gasPrice": w3.toWei("25", "gwei"),
    "nonce": nonce,
    "chainId": 43113  # Fuji Testnet Chain ID
})

# --- Sign and send transaction ---
signed_txn = w3.eth.account.signTransaction(txn, private_key)
tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
print(f"Transaction sent! Hash: {tx_hash.hex()}")

# --- Wait for confirmation ---
receipt = w3.eth.waitForTransactionReceipt(tx_hash)

if receipt.status == 1:
    print("NFT minted successfully!")
else:
    print("Transaction failed.")
