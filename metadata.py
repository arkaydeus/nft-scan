import asyncio
import json
import time
from functools import reduce
from typing import List, Tuple

import aiohttp
import pandas as pd

from progress import Progress


def generate_urls_from_stub(stub: str, iterable, gateway, http=False, suffix=None):
    if stub[:7] == "ipfs://":
        if http:
            stub = f"http://{gateway}/ipfs/" + stub[7:]
        else:
            stub = f"https://{gateway}/ipfs/" + stub[7:]
    if suffix:
        return [(index, stub + str(index) + suffix) for index in iterable]
    else:
        return [(index, stub + str(index)) for index in iterable]


async def get_metadata(
    session: aiohttp.ClientSession, url: str, index: int, progress: Progress
):
    """Get an individual metadata JSON dictionary"""
    if url:
        async with session.get(url) as response:
            if response.status == 200:
                json_response = await response.json()
                progress.increment()
                return (index, json_response)
            else:
                print(index, response.status)
                if response.status == 429:
                    raise Exception("Rate limited")
    return (index, None)


async def get_all_json_objects(
    urls: List[Tuple[int, str]], limit: int = 10, timeout: int = 180
):
    """Get all the JSON dictionaries for each token in the list"""

    conn = aiohttp.TCPConnector(limit=limit)
    timeout = aiohttp.ClientTimeout(total=timeout)

    progress = Progress(len(urls))

    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        responses: List = await asyncio.gather(
            *(get_metadata(session, url[1], url[0], progress) for url in urls)
        )

    progress.update_progress(1)
    return responses


def process_json(blobs):
    """Process JSON objects into a list of dicts"""
    data_list = []
    for item in blobs:
        input_dict = item[1]
        try:
            attributes = input_dict["attributes"]
            item_dict = {}
            item_dict["index"] = item[0]
            for attribute in attributes:
                item_dict[attribute["trait_type"]] = attribute["value"]
            data_list.append(item_dict)
        except:
            print("Problem with:", item[0])
            print(item)

    return data_list


def save_data_list(data_list, filename):
    with open(f"{filename}.json", "w+") as f:
        f.write(json.dumps(data_list, indent=2))
    print(f"Written {filename}.json")


def load_data_list(filename):
    with open(f"{filename}.json", "r") as f:
        return json.loads(f.read())
        print("Loaded file")


def build_dataframe(data_list, categorical=True, contract: str = ""):
    df = pd.DataFrame(data_list)
    df.set_index("index", inplace=True)

    for col in df.columns:
        df[col] = df[col].apply(str)
        df.loc[(df[col].isin(["nan", ""])), col] = "None"
        lookup_table = df[col].value_counts(dropna=False)
        component_series = df[col].map(lookup_table).astype("int64")
        component_series = component_series.apply(str)
        df[col].apply(str)
        new_col = df[col] + " (" + component_series + ")"
        if categorical:
            df[col] = new_col.astype("category")
        else:
            df[col] = new_col

    rarity_components = []
    for col in df.columns:
        lookup_table = len(df[col]) / df[col].value_counts(dropna=False)
        component_series = df[col].map(lookup_table).astype("float64")
        rarity_components.append(component_series)

    if rarity_components:

        df["Rarity score"] = reduce(lambda x, y: x.add(y), rarity_components)
        df["Standard score"] = ((df["Rarity score"]) / df["Rarity score"].std()).round(
            3
        )
        df["Rank"] = df["Rarity score"].rank(ascending=False)
        df["Rarity score"] = df["Rarity score"].map("{:,.0f}".format)
        df["OS link"] = (
            "https://opensea.io/assets/" + contract + "/" + df.index.astype("str")
        )

        return df.sort_values("Rank")

    else:
        return
