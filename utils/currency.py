import aiohttp
import asyncio
from config import config


async def fetch_simple_price(ids: str, vs_currencies: str) -> dict:
    url = f"https://api.coingecko.com/api/v3/simple/price?vs_currencies={vs_currencies}&ids={ids}"
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": f"{config.COINGECKO_API_KEY.get_secret_value()}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            return data


