import random
import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.providers.rpc import HTTPProvider


def connect_to_eth():
	url = "https://eth-mainnet.alchemyapi.io/v2/nQJ9TgR6pevl6wI46LXFC6-18lZBQzQ9"  # FILL THIS IN
	w3 = Web3(HTTPProvider(url))
	assert w3.is_connected(), f"Failed to connect to provider at {url}"
	return w3


def connect_with_middleware(contract_json):
	with open(contract_json, "r") as f:
		d = json.load(f)
		d = d['bsc']
		address = d['address']
		abi = d['abi']

	bnb_url = "https://bnb-testnet.g.alchemy.com/v2/ARsMoB4Uug9pZ_gUAMolg"  # FILL THIS IN
	w3 = Web3(HTTPProvider(bnb_url))
	assert w3.is_connected(), f"Failed to connect to provider at {bnb_url}"

	w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
	contract = w3.eth.contract(address=address, abi=abi)
	return w3, contract


def is_ordered_block(w3, block_num):
	"""
	Takes a block number
	Returns a boolean that tells whether all the transactions in the block are ordered by priority fee
	"""
	block = w3.eth.get_block(block_num, full_transactions=True)
	base_fee = block.get("baseFeePerGas", 0)
	priority_fees = []

	for tx in block.transactions:
		tx_type = tx.get("type")
		
		# Type 0
		if tx_type is None or tx_type == "0x0":

			if base_fee == 0:
				priority_fee = tx.gasPrice
			else:
				priority_fee = tx.gasPrice - base_fee

		# Type 2
		elif tx_type == "0x2":

			max_priority = tx.get("maxPriorityFeePerGas")
			max_fee = tx.get("maxFeePerGas")

			if max_priority is not None and max_fee is not None:
				priority_fee = min(max_priority, max_fee - base_fee)
			else:
				priority_fee = tx.gasPrice - base_fee

		priority_fees.append(priority_fee)

	# Now check if the list is sorted in decreasing order
	ordered = True
	for i in range(len(priority_fees) - 1):
		if priority_fees[i] < priority_fees[i + 1]:
			ordered = False
			break

	return ordered


def get_contract_values(contract, admin_address, owner_address):
	"""
	Takes a contract object, and two addresses (as strings) to be used for calling
	the contract to check current on chain values.
	"""
	default_admin_role = int.to_bytes(0, 32, byteorder="big")

	# TODO complete the following lines by performing contract calls
	onchain_root = contract.functions.merkleRoot().call()  # Get and return the merkleRoot from the provided contract
	has_role = contract.functions.hasRole(default_admin_role, admin_address).call()  # Check the contract to see if the address "admin_address" has the role "default_admin_role"
	prime = contract.functions.getPrimeByOwner(owner_address).call()  # Call the contract to get the prime owned by "owner_address"

	return onchain_root, has_role, prime


if __name__ == "__main__":
	admin_address = "0xAC55e7d73A792fE1A9e051BDF4A010c33962809A"
	owner_address = "0x793A37a85964D96ACD6368777c7C7050F05b11dE"
	contract_file = "contract_info.json"

	eth_w3 = connect_to_eth()
	cont_w3, contract = connect_with_middleware(contract_file)

	latest_block = eth_w3.eth.get_block_number()
	london_hard_fork_block_num = 12965000
	assert latest_block > london_hard_fork_block_num, f"Error: the chain never got past the London Hard Fork"

	n = 5
	for _ in range(n):
		block_num = random.randint(1, latest_block)
		ordered = is_ordered_block(eth_w3, block_num)
		if ordered:
			print(f"Block {block_num} is ordered")
		else:
			print(f"Block {block_num} is not ordered")
