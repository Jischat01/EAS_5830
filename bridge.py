from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware # Necessary for POA chains
from datetime import datetime
import json
import pandas as pd
from eth_account import Account


def connect_to(chain):
    if chain == 'source':  # The source contract chain is avax
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet

    if chain == 'destination':  # The destination contract chain is bsc
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet

    if chain in ['source', 'destination']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info):
    """
        Load the contract_info file into a dictionary
        This function is used by the autograder and will likely be useful to you
    """
    try:
        with open(contract_info, 'r') as f:
            contracts = json.load(f)
    except Exception as e:
        print(f"Failed to read contract info\nPlease contact your instructor\n{e}")
        return 0
    return contracts[chain]


def scan_blocks(chain, contract_info="contract_info.json"):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    # This is different from Bridge IV where chain was "avax" or "bsc"
    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return 0

    # Load contract info
    source_info = get_contract_info('source', contract_info)
    destination_info = get_contract_info('destination', contract_info)

    # Connect to both chains
    w3_source = connect_to('source')
    w3_dest = connect_to('destination')

    # Load private key from file
    try:
        with open("secret_key.txt", "r") as f:
            warden_key = f.read().strip()
    except Exception as e:
        print("❌ Failed to read secret_key.txt:", e)
        return 0

    warden_account = Account.from_key(warden_key)
    warden_address = warden_account.address

    # Select source/destination directions
    if chain == 'source':
        w3_from = w3_source
        w3_to = w3_dest
        from_info = source_info
        to_info = destination_info
        event_name = "Deposit"
    else:
        w3_from = w3_dest
        w3_to = w3_source
        from_info = destination_info
        to_info = source_info
        event_name = "Unwrap"

    from_contract = w3_from.eth.contract(address=from_info["address"], abi=from_info["abi"])
    to_contract = w3_to.eth.contract(address=to_info["address"], abi=to_info["abi"])

    latest = w3_from._
