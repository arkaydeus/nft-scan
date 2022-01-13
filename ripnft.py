import argparse
import asyncio
from datetime import datetime
from typing import List

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
        "ipfs.io",
        http=False,
        suffix=suffix,
    )
    start = datetime.now()
    blobs = await get_all_json_objects(urls, limit=6, timeout=600)
    print(f"\nDownloaded data: {str(datetime.now() - start)[2:][:-3]}")
    return process_json(blobs)


def data_frame(data_list):
    start = datetime.now()
    df = build_dataframe(data_list, categorical=False)
    print(
        f"Built dataframe and calculated stats: {str(datetime.now() - start)[2:][:-3]}"
    )

    return df


async def main(args):
    if args.ipfs:
        url = f"ipfs://{args.url}/"
    else:
        url = args.url
    data = await get_data(url=url, limit=args.limit, suffix=args.suffix)
    df: DataFrame = data_frame(data)
    df.to_excel("output.xlsx")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Rip an NFT collection.")
    parser.add_argument("url", help="The url to scan", type=str)
    parser.add_argument("limit", help="How many tokens to scan (from 0)", type=int)
    parser.add_argument("--suffix", help="filename suffix such as .json", type=str)
    parser.add_argument("--ipfs", help="Use url as IPFS hash", action="store_true")
    args = parser.parse_args()
    if args.url and args.limit:
        asyncio.run(main(args))

# "ipfs://QmNN69NeVQJ3iCscZvxgrzdUdRuXD3E7gRZWesDcEjpPTt/"
