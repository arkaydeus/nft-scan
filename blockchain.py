import sys
from concurrent.futures import ThreadPoolExecutor

import aiohttp
from web3 import Web3
from web3.eth import Contract

ABI_ENDPOINT = "https://api.etherscan.io/api?module=contract&action=getabi&address="


async def get_abi(contract):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{ABI_ENDPOINT}{contract}") as response:
            response.raise_for_status()
            response_data = await response.json()

            return response_data["result"]


async def get_w3_contract(str_address: str, provider: str):
    """Gets a Web3 contract object to interact with"""
    abi = await get_abi(str_address)
    address = Web3.toChecksumAddress(str_address)
    w3 = Web3(Web3.HTTPProvider(provider))
    return w3.eth.contract(address=address, abi=abi)


def get_metadata_urls(contract: Contract, maximum: int = None):
    """Retrieve all tokenURI results for a contract"""

    def task(index):
        try:
            contract_data = contract.functions.tokenURI(index).call()
            if contract_data[:7] == "ipfs://":
                contract_data = "https://ipfs.io/ipfs/" + contract_data[7:]
            return (index, contract_data)
        except Exception as e:
            print(e, "Error at", index)
            tb = sys.exc_info()[2]
            print(e.with_traceback(tb))
        return (index, None)

    with ThreadPoolExecutor(max_workers=100) as executor:
        total_tokens = contract.functions.totalSupply().call() + 1
        if maximum:
            total_tokens = min(total_tokens, maximum)
        results = executor.map(task, range(total_tokens))
    return list(results)


def get_individual_token_url(contract: Contract, index: int):
    try:
        contract_data = contract.functions.tokenURI(index).call()
        if contract_data[:7] == "ipfs://":
            contract_data = "https://ipfs.io/ipfs/" + contract_data[7:]
        return (index, contract_data)
    except Exception as e:
        print(e, "Error at", index)
        tb = sys.exc_info()[2]
        print(e.with_traceback(tb))
    return (index, None)
