#!/usr/bin/env python3
import json
import sys
from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account

BLOCK_WINDOW  = 5
GAS_AVAX      = 300_000
GAS_BSC       = 3_000_000
CONTRACT_INFO = "contract_info.json"
SECRET_KEY    = "secret_key.txt"

def connect_to(chain: str) -> Web3:
    if chain == "source":
        url = "https://api.avax-test.network/ext/bc/C/rpc"
    elif chain == "destination":
        url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
    else:
        raise ValueError(f"Unknown chain '{chain}'")
    w3 = Web3(HTTPProvider(url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3

def load_contracts(path: str):
    with open(path) as f:
        data = json.load(f)
    return data["source"], data["destination"]

def load_warden(path: str):
    with open(path) as f:
        pk = f.read().strip()
    return Account.from_key(pk)

def send_tx(w3: Web3, acct: Account, fn, gas_limit: int):
    nonce    = w3.eth.get_transaction_count(acct.address, "pending")
    gasprice = w3.eth.gas_price
    chain_id = w3.eth.chain_id
    tx = fn.build_transaction({
        "from": acct.address,
        "nonce": nonce,
        "gas": gas_limit,
        "gasPrice": gasprice,
        "chainId": chain_id
    })
    signed = acct.sign_transaction(tx)
    raw_bytes = getattr(signed, "rawTransaction", None) \
             or getattr(signed, "raw_transaction", None) \
             or signed.get("rawTransaction") \
             or signed.get("raw_transaction")
    raw_hex = Web3.toHex(raw_bytes)
    txh = w3.eth.send_raw_transaction(raw_hex)
    return w3.eth.wait_for_transaction_receipt(txh)

def scan_blocks(chain: str, contract_info_path: str = CONTRACT_INFO):
    src_info, dst_info = load_contracts(contract_info_path)
    w3_src = connect_to("source")
    w3_dst = connect_to("destination")
    warden = load_warden(SECRET_KEY)

    if chain == "source":
        w3_from, w3_to   = w3_src, w3_dst
        from_info, to_info = src_info, dst_info
        event_name       = "Deposit"
        action_fn        = lambda c,t,r,a: c.functions.wrap(t, r, a)
        gas_limit        = GAS_BSC
    else:
        w3_from, w3_to   = w3_dst, w3_src
        from_info, to_info = dst_info, src_info
        event_name       = "Unwrap"
        action_fn        = lambda c,t,r,a: c.functions.withdraw(t, r, a)
        gas_limit        = GAS_AVAX

    from_c = w3_from.eth.contract(address=from_info["address"], abi=from_info["abi"])
    to_c   = w3_to  .eth.contract(address=to_info  ["address"], abi=to_info  ["abi"])

    evt_abi = next(e for e in from_info["abi"]
                   if e.get("type")=="event" and e.get("name")==event_name)
    types   = [inp["type"] for inp in evt_abi["inputs"]]
    sig     = f"{event_name}({','.join(types)})"
    topic0  = Web3.keccak(text=sig).hex()

    latest = w3_from.eth.block_number
    start  = max(0, latest - BLOCK_WINDOW)
    logs   = w3_from.eth.get_logs({
        "address":   from_info["address"],
        "fromBlock": start,
        "toBlock":   latest,
        "topics":    [topic0]
    })

    for log in logs:
        handler = getattr(from_c.events, event_name)
        evt     = handler().processLog(log)
        args    = evt["args"]

        if event_name == "Deposit":
            token = args["token"]
            rec   = args["recipient"]
            amt   = args["amount"]
            print(f"▶️ Deposit→wrap({token}, {rec}, {amt})")
        else:
            token = args["underlying_token"]
            rec   = args["to"]
            amt   = args["amount"]
            print(f"▶️ Unwrap→withdraw({token}, {rec}, {amt})")

        fn      = action_fn(to_c, token, rec, amt)
        receipt = send_tx(w3_to, warden, fn, gas_limit)
        status  = "✅" if receipt.status == 1 else "❌"
        print(f"   {status} tx hash: {receipt.transactionHash.hex()}")

if __name__ == "__main__":
    if len(sys.argv)!=2 or sys.argv[1] not in ("source","destination"):
        print("Usage: python bridge.py [source|destination]")
        sys.exit(1)
    scan_blocks(sys.argv[1])
