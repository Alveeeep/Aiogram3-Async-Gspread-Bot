import asyncio
from datetime import datetime
from loguru import logger
from config import config
import gspread_asyncio
from gspread_asyncio import AsyncioGspreadWorksheet
from utils.re_msg import parse_message
# from google-auth package
from google.oauth2.service_account import Credentials


def get_creds():
    try:
        creds = Credentials.from_service_account_file(config.SERVICE_ACCOUNT_FILE.get_secret_value())
        scoped = creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets"
        ])
        return scoped
    except Exception as e:
        logger.error(f"Failed to get credentials: {e}")
        raise


async def get_last_row(worksheet: AsyncioGspreadWorksheet, start_col_index):
    try:
        col_values = await worksheet.col_values(start_col_index)
        last_filled_row = len(col_values)
        next_row = last_filled_row + 1
        logger.debug(f"Found last row: {last_filled_row} for column {start_col_index}")
        return next_row
    except Exception as e:
        logger.error(f"Failed to get last row: {e}")
        raise


async def add_record_to_table(worksheet: AsyncioGspreadWorksheet, next_row, new_data, start_col_index, end_col_index=0):
    def col_num_to_letter(n):
        result = ''
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            result = chr(65 + remainder) + result
        return result

    try:
        start_col_letter = col_num_to_letter(start_col_index)
        start_cell = f"{start_col_letter}{next_row}"
        if end_col_index > 0:
            end_col_letter = col_num_to_letter(end_col_index)
            end_cell = f"{end_col_letter}{next_row}"
            cell_range = f"{start_cell}:{end_cell}"
        else:
            cell_range = start_cell

        logger.debug(f"Adding data to range {cell_range}: {new_data}")
        await worksheet.update([new_data], cell_range)
        logger.info(f"Successfully added data to row {next_row}")
    except Exception as e:
        logger.error(f"Failed to add record: {e}")
        raise


agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)


async def write_for_change_usdt(message: str):
    logger.info("Processing USDT exchange message")
    agc = await agcm.authorize()
    exchanges = await agc.open_by_key(config.SHEET_ID.get_secret_value())
    aws = await exchanges.worksheet('Обмены')
    tranz = await exchanges.worksheet('Транзакции')
    data = await parse_message(message)
    logger.debug(f"Parsed message data: {data}")
    part_one = [datetime.now().strftime("%d.%m.%Y"), data.get('Сумма usdt'),
                data.get('Сумма в фиате') + ' ' + data.get('Валюта'),
                f'=1 / GOOGLEFINANCE("CURRENCY:USDT{data.get('Валюта')}")']
    if 'Покупка' in data.get('Тип'):
        part_two = [data.get('Менеджер')]
        if 'CHF' in data.get('Валюта'):
            last_row = await get_last_row(aws, 23)
            await add_record_to_table(aws, last_row, part_one, 23, 26)
            await add_record_to_table(aws, last_row, part_two, start_col_index=30)
        elif 'EUR' in data.get('Валюта'):
            last_row = await get_last_row(aws, 34)
            await add_record_to_table(aws, last_row, part_one, 34, 37)
            await add_record_to_table(aws, last_row, part_two, start_col_index=41)
        # Часть Транзакций
        last_row = await get_last_row(tranz, 1)
        data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('Сумма usdt'), 'Внешний источник',
                       data.get('Источник сделки')]
        await add_record_to_table(tranz, last_row, data_to_add, 1, 4)
        data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('Сумма в фиате'), data.get('Фиат счёт'),
                       'Внешний источник']
        await add_record_to_table(tranz, last_row + 1, data_to_add, 1, 4)
    else:
        part_two = [data.get('Фиат счёт'), data.get('Менеджер')]
        if 'CHF' in data.get('Валюта'):
            last_row = await get_last_row(aws, 1)
            await add_record_to_table(aws, last_row, part_one, 1, 4)
            await add_record_to_table(aws, last_row, part_two, 8, 9)
        elif 'EUR' in data.get('Валюта'):
            last_row = await get_last_row(aws, 12)
            await add_record_to_table(aws, last_row, part_one, 12, 15)
            await add_record_to_table(aws, last_row, part_two, 19, 20)
        # Часть Транзакций
        last_row = await get_last_row(tranz, 1)
        data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('Сумма usdt'), data.get('Источник сделки'),
                       'Внешний источник']
        await add_record_to_table(tranz, last_row, data_to_add, 1, 4)
        data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('Сумма в фиате'), 'Внешний источник',
                       data.get('Фиат счёт')]
        await add_record_to_table(tranz, last_row + 1, data_to_add, 1, 4)
        logger.info("Successfully processed USDT exchange")


async def write_for_change_other(message: str):
    logger.info("Processing OTHER exchange message")
    agc = await agcm.authorize()
    exchanges = await agc.open_by_key(config.SHEET_ID.get_secret_value())
    aws = await exchanges.worksheet('Обмены')
    tranz = await exchanges.worksheet('Транзакции')
    data = await parse_message(message)
    logger.debug(f"Parsed message data: {data}")
    get = 0
    gave = 0
    curr = "CHFEUR"
    # тут расчет что это транзакция типа покупка chf за eur
    if 'Покупка CHF за EUR' in data.get('Тип'):
        get = data.get('Сумма CHF')
        gave = data.get('Сумма EUR')
    elif 'Покупка EUR за CHF' in data.get('Тип'):
        get = data.get('Сумма EUR')
        gave = data.get('Сумма CHF')
        curr = "EURCHF"
    part_one = [datetime.now().strftime("%d.%m.%Y"), get,
                gave,
                f'=1 / GOOGLEFINANCE("CURRENCY:{curr}")']
    last_row = await get_last_row(aws, 45)
    await add_record_to_table(aws, last_row, part_one, 45, 48)
    # Часть Транзакций
    last_row = await get_last_row(tranz, 1)
    data_to_add = [datetime.now().strftime("%d.%m.%Y"), gave, data.get('Счёт отправки'),
                   'Внешний источник']
    await add_record_to_table(tranz, last_row, data_to_add, 1, 4)
    data_to_add = [datetime.now().strftime("%d.%m.%Y"), get, 'Внешний источник',
                   data.get('Счёт получения')]
    await add_record_to_table(tranz, last_row + 1, data_to_add, 1, 4)
    logger.info("Successfully processed OTHER exchange")


async def write_for_internal_transfer(message: str):
    logger.info("Processing internal transfer message")
    agc = await agcm.authorize()
    transactions = await agc.open_by_key(config.SHEET_ID.get_secret_value())
    aws = await transactions.worksheet('Транзакции')
    data = await parse_message(message)
    logger.debug(f"Parsed message data: {data}")
    last_row = await get_last_row(aws, 1)
    data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('Сумма'), data.get('Счёт откуда'),
                   data.get('Счёт куда'), data.get('Комментарий')]
    await add_record_to_table(aws, last_row, data_to_add, 1, 5)
    logger.info("Successfully processed internal transfer")


async def write_for_oborotka(message: str):
    logger.info("Processing oborotka message")
    agc = await agcm.authorize()
    oborotka = await agc.open_by_key(config.SHEET_ID.get_secret_value())
    aws = await oborotka.worksheet('Оборотка')
    data = await parse_message(message)
    logger.debug(f"Parsed message data: {data}")
    last_row = await get_last_row(aws, 1)
    data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('Сумма'), data.get('Валюта'),
                   data.get('Бенефициар'), data.get('Комментарий')]
    await add_record_to_table(aws, last_row, data_to_add, 1, 5)
    logger.info("Successfully processed oborotka")
