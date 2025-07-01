import asyncio
from config import config
import gspread_asyncio

# from google-auth package
from google.oauth2.service_account import Credentials


def get_creds():
    # To obtain a service account JSON file, follow these steps:
    # https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account
    creds = Credentials.from_service_account_file(config.SERVICE_ACCOUNT_FILE.get_secret_value())
    scoped = creds.with_scopes([
        "https://www.googleapis.com/auth/spreadsheets"
    ])
    return scoped

agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

async def write_for_change_usdt(message: str):
    agc = await agcm.authorize()
    exchanges = await agc.open_by_key(config.SHEET_ID.get_secret_value())
    aws = await exchanges.worksheet('Обмены')
    if 'Покупка' in message:
        await aws
    else:
        await aws.update_cell()


async def write_for_change_other(message: str):
    agc = await agcm.authorize()
    exchanges = await agc.open_by_key(config.SHEET_ID.get_secret_value())
    aws = await exchanges.worksheet('Обмены')

async def write_for_internal_transfer(message: str):
    agc = await agcm.authorize()
    transactions = await agc.open_by_key(config.SHEET_ID.get_secret_value())
    aws = await transactions.worksheet('Транзакции')

async def write_for_oborotka(message: str):
    agc = await agcm.authorize()
    oborotka = await agc.open_by_key(config.SHEET_ID.get_secret_value())
    aws = await oborotka.worksheet('Оборотка')
