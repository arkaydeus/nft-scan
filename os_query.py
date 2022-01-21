from dataclasses import dataclass
from typing import Dict, List, Optional

import aiohttp


@dataclass
class OsAsset(object):
    contract: str
    token_id: str
    num_sales: int
    image_url: str
    image_thumbnail_url: str
    name: str
    description: str
    permalink: str
    collection_slug: str
    current_price: float
    last_sale_time: str
    last_sale_price: float
    above_floor: Optional[float] = None


def from_gwei(gwei: float) -> float:
    """Converts a value from GWEI to ETH
    by dividing by 1000000000000000000

    Args:
        gwei (float): Gwei value

    Returns:
        float: Eth value
    """

    if isinstance(gwei, str):
        gwei = float(gwei)

    return gwei / 1000000000000000000


async def get_os_assets(
    token_ids: List[str], contract: str = None, collection_key: str = None
):
    """Retrieves assets from OS API for a given contract and list of token_ids
    Must use either contract address or collection key

    Args:
        token_ids (List[str]): [description]
        contract (str): Contract address
        collection_key (str): Collection key

    Returns:
        [type]: [description]
    """

    token_id_str = "?token_ids=" + "&token_ids=".join(token_ids)

    if contract:
        url = f"https://api.opensea.io/api/v1/assets{token_id_str}&asset_contract_address={contract}&order_direction=desc&offset=0&limit=50"
    elif collection_key:
        url = f"https://api.opensea.io/api/v1/assets{token_id_str}&collection={collection_key}&order_direction=desc&offset=0&limit=50"
    else:
        return

    async with aiohttp.ClientSession() as session:
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
        }
        async with session.get(url, headers=headers) as response:

            response_data: Dict = await response.json()
            if response.status == 200:

                assets = []
                response_list = response_data["assets"]

                asset: dict
                for asset in response_list:
                    token_id: str = asset.get("token_id", "")
                    num_sales: int = asset.get("num_sales", 0)
                    image_url: str = asset.get("image_url", "")
                    image_thumbnail_url: str = asset.get("image_thumbnail_url", "")
                    name: str = asset.get("name", "")
                    description: str = asset.get("description", "")
                    permalink: str = asset.get("permalink", "")
                    collection_slug: str = asset["collection"].get("slug", "")
                    if asset["sell_orders"]:
                        current_price: float = from_gwei(
                            asset["sell_orders"][0].get("current_price", 0)
                        )
                    else:
                        current_price = None

                    if asset["last_sale"]:
                        last_sale_time: str = asset["last_sale"].get(
                            "event_timestamp", ""
                        )
                        last_sale_price: float = from_gwei(
                            asset["last_sale"].get("total_price", 0)
                        )
                    else:
                        last_sale_time = None
                        last_sale_price = None

                    assets.append(
                        OsAsset(
                            contract=contract,
                            token_id=token_id,
                            num_sales=num_sales,
                            image_url=image_url,
                            image_thumbnail_url=image_thumbnail_url,
                            name=name,
                            description=description,
                            permalink=permalink,
                            collection_slug=collection_slug,
                            current_price=current_price,
                            last_sale_time=last_sale_time,
                            last_sale_price=last_sale_price,
                        )
                    )
                return assets

            else:
                return response
