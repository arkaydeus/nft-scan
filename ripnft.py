import argparse
import asyncio
from datetime import datetime
from typing import List
from os_query import OsAsset, get_os_assets
from pandas import DataFrame

from metadata import (
    build_dataframe,
    generate_urls_from_stub,
    get_all_json_objects,
    process_json,
)


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
    print("Enter contract address e.g. 0x9372b371196751dd2F603729Ae8D8014BbeB07f6")
    contract: str = input()
    print("Enter full url e.g. ipfs://QmNN69NeVQJ3iCscZvxgrzdUdRuXD3E7gRZWesDcEjpPTt/")
    url: str = input()
    print("Enter limit for how many tokens e.g. 100")
    limit: int = int(input())
    print(
        "Enter filename suffix e.g. .json (including the dot) or hit enter if nothing"
    )
    suffix: str = input()
    asyncio.run(main(url, limit, suffix, contract))


# "ipfs://QmNN69NeVQJ3iCscZvxgrzdUdRuXD3E7gRZWesDcEjpPTt/"
