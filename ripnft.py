import argparse
import asyncio
from datetime import datetime
from typing import List
import sys

from decouple import config
from pandas import DataFrame

from metadata import (
    build_dataframe,
    generate_urls_from_stub,
    get_all_json_objects,
    process_json,
)
from os_query import OsAsset, get_os_assets
import blockchain


async def get_data(url: str, limit: int, suffix: str):
    urls: List[tuple] = generate_urls_from_stub(
        url,
        range(limit),
        # "127.0.0.1:8080",
        "ipfs.io",
        http=False,
        suffix=suffix,
    )
    start = datetime.now()
    blobs = await get_all_json_objects(urls, limit=6, timeout=600)
    print(f"\nDownloaded data: {str(datetime.now() - start)[2:][:-3]}")
    return process_json(blobs)


def data_frame(data_list, contract: str):
    start = datetime.now()
    df = build_dataframe(data_list, categorical=False, contract=contract)

    print(
        f"Built dataframe and calculated stats: {str(datetime.now() - start)[2:][:-3]}"
    )

    return df


async def main(url: str, limit: int, suffix: str, contract: str):
    # if args.ipfs:
    #     url = f"ipfs://{args.url}/"
    # else:
    #     url = args.url
    data = await get_data(url=url, limit=limit, suffix=suffix)
    df: DataFrame = data_frame(data, contract)

    if df is None:
        print("No dataframe built. Likely no attributes yet.")
        return

    filename = f"output/output {str(datetime.now())} no-price.xlsx"
    df.to_excel(filename)

    tokens = [str(x) for x in df.head(30).index]

    asset: OsAsset
    assets = await get_os_assets(tokens, contract=contract)

    if assets:

        for asset in assets:
            df.loc[df.index == int(asset.token_id), "Price"] = asset.current_price

        filename = f"output/output {str(datetime.now())} with-price.xlsx"
        df.to_excel(filename)


def clean_url(input_url: str) -> str:
    """Removes the end of the url

    Args:
        input_url (str): Url from getURI

    Returns:
        [type]: Clean URL without token specific extension
    """
    components = input_url.split("/")[:-1]
    return "/".join(components) + "/"


def get_suffix(input_url: str) -> str:
    """Extract the suffix from a url

    Args:
        input_url (str): URL from get URI

    Returns:
        str: Just the suffix
    """
    last_section = input_url.split("/")[-1:]
    components = last_section[0].split(".")
    if len(components) > 1:
        return "." + components[-1:][0]


def check_input(message: str, default_val: str):
    print(message, default_val)
    print("Hit enter to accept or enter new value.")
    input_str = input()

    if input_str != "":
        return input_str
    else:
        return default_val


def check_bad_ipfs(url: str):

    url = url.lower()
    if "ipfs" in url:

        if url[:7] != "ipfs://" and url[:21] != "https://ipfs.io/ipfs/":
            print(
                "Warning - an IPFS link has been detected but it is not using ipfs:// syntax."
            )
            print(
                "Please reformat like this: ipfs://QmNN69NeVQJ3iCscZvxgrzdUdRuXD3E7gRZWesDcEjpPTt/"
            )


def get_variables(provider: str):
    print("Enter contract address e.g. 0x9372b371196751dd2F603729Ae8D8014BbeB07f6")
    contract_address: str = input()

    url_root: str = ""
    suffix: str = ""

    try:
        contract = asyncio.run(blockchain.get_w3_contract(contract_address, provider))
        metadata_url = blockchain.get_individual_token_url(contract, 1)[1]
        try:
            url_root = clean_url(metadata_url)
            suffix = get_suffix(metadata_url)
        except:
            print("Error automatically extracting ")
            raise
    except:
        print("Error reading blockchain. Check provider (e.g. Infura)")
        raise

    check_bad_ipfs(metadata_url)

    url_root = check_input("URL expected to be", url_root)
    suffix = check_input("Suffix expected to be", suffix)

    print("Enter limit for how many tokens e.g. 100")
    limit: int = int(input())

    return url_root, suffix, limit, contract_address


if __name__ == "__main__":

    # parser = argparse.ArgumentParser(description="Rip an NFT collection.")
    # parser.add_argument("url", help="The url to scan", type=str)
    # parser.add_argument("limit", help="How many tokens to scan (from 0)", type=int)
    # parser.add_argument("--suffix", help="filename suffix such as .json", type=str)
    # parser.add_argument("--ipfs", help="Use url as IPFS hash", action="store_true")
    # args = parser.parse_args()
    # if args.url and args.limit:
    #     print("Called with", args.url, args.limit)
    #     asyncio.run(main(args))
    # else:

    INFURA_URL = config("INFURA_URL")

    if INFURA_URL is None:
        print(
            "You must set INFURA_URL env. variable. e.g. https://mainnet.infura.io/v3/YOUR_TOKEN_HERE"
        )

    url_root, suffix, limit, contract_address = get_variables(INFURA_URL)

    asyncio.run(main(url_root, limit, suffix, contract_address))
