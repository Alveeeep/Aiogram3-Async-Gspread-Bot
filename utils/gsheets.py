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


async def get_current_exchange_rate(worksheet: AsyncioGspreadWorksheet, curr: str):
    # Сначала получаем текущее значение курса
    formula = f"=1 / GOOGLEFINANCE(\"CURRENCY:USDT{curr}\")"

    # Временная запись формулы для получения значения
    await worksheet.update_acell('BA5', formula)

    # Ждем немного для расчета
    await asyncio.sleep(2)

    # Получаем вычисленное значение
    cell_value = await worksheet.acell('BA5', value_render_option='FORMATTED_VALUE')
    current_rate = cell_value.value

    # Очищаем временную ячейку
    await worksheet.update_acell('BA5', '')

    return current_rate


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
        await worksheet.update([new_data], cell_range, value_input_option='USER_ENTERED')
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
    part_one = [datetime.now().strftime("%d.%m.%Y"), data.get('сумма usdt'),
                data.get('сумма в фиате'), await get_current_exchange_rate(aws, data.get('валюта'))]
    if 'Покупка' in data.get('тип'):
        part_two = [data.get('источник сделки', 'Binance'), data.get('из бота')]
        part_three = [data.get('менеджер')]
        if 'CHF' in data.get('валюта'):
            last_row = await get_last_row(aws, 28)
            await add_record_to_table(aws, last_row, part_one, 28, 31)
            await add_record_to_table(aws, last_row, part_two, 35, 36)
            await add_record_to_table(aws, last_row, part_three, start_col_index=38)
        elif 'EUR' in data.get('валюта'):
            last_row = await get_last_row(aws, 41)
            await add_record_to_table(aws, last_row, part_one, 41, 44)
            await add_record_to_table(aws, last_row, part_two, 48, 49)
            await add_record_to_table(aws, last_row, part_three, start_col_index=51)
        # Часть Транзакций
        last_row = await get_last_row(tranz, 1)
        data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('сумма usdt'), 'Внешний источник',
                       data.get('источник сделки', 'Binance')]
        await add_record_to_table(tranz, last_row, data_to_add, 1, 4)
        data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('сумма в фиате'), data.get('фиат счёт'),
                       'Внешний источник']
        await add_record_to_table(tranz, last_row + 1, data_to_add, 1, 4)
    else:
        part_one = [datetime.now().strftime("%d.%m.%Y"),data.get('сумма в фиате'),
                    data.get('сумма usdt'), await get_current_exchange_rate(aws, data.get('валюта'))]
        part_three = [data.get('менеджер')]
        if 'CHF' in data.get('валюта'):
            part_two = [data.get('фиат счёт'), data.get('источник сделки', 'Binance'), data.get('из бота')]
            last_row = await get_last_row(aws, 1)
            await add_record_to_table(aws, last_row, part_one, 1, 4)
            await add_record_to_table(aws, last_row, part_two, 8, 10)
            await add_record_to_table(aws, last_row, part_three, start_col_index=12)
        elif 'EUR' in data.get('валюта'):
            part_two = [data.get('источник сделки', 'Binance'), data.get('из бота')]
            last_row = await get_last_row(aws, 15)
            await add_record_to_table(aws, last_row, part_one, 15, 18)
            await add_record_to_table(aws, last_row, part_two, 22, 23)
            await add_record_to_table(aws, last_row, part_three, start_col_index=25)
        # Часть Транзакций
        data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('сумма usdt'),
                       data.get('источник сделки', 'Binance'),
                       'Внешний источник']
        await add_record_to_table(tranz, await get_last_row(tranz, 1), data_to_add, 1, 4)
        data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('сумма в фиате'), 'Внешний источник',
                       data.get('фиат счёт')]
        await add_record_to_table(tranz, await get_last_row(tranz, 1), data_to_add, 1, 4)
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
    index = 0
    curr = "CHFEUR"
    # тут расчет что это транзакция типа покупка chf за eur
    if 'Покупка CHF за EUR' in data.get('тип'):
        get = data.get('сумма chf')
        gave = data.get('сумма eur')
        index = 54
    elif 'Покупка EUR за CHF' in data.get('тип'):
        get = data.get('сумма eur')
        gave = data.get('сумма chf')
        curr = "EURCHF"
        index = 62
    part_one = [datetime.now().strftime("%d.%m.%Y"), get,
                gave, await get_current_exchange_rate(aws, curr)]
    last_row = await get_last_row(aws, index)
    await add_record_to_table(aws, last_row, part_one, index, index + 3)
    # Часть Транзакций
    data_to_add = [datetime.now().strftime("%d.%m.%Y"), gave, data.get('счёт отправки'),
                   'Внешний источник']
    await add_record_to_table(tranz, await get_last_row(tranz, 1), data_to_add, 1, 4)
    data_to_add = [datetime.now().strftime("%d.%m.%Y"), get, 'Внешний источник',
                   data.get('счёт получения')]
    await add_record_to_table(tranz, await get_last_row(tranz, 1), data_to_add, 1, 4)
    logger.info("Successfully processed OTHER exchange")


async def write_for_internal_transfer(message: str):
    logger.info("Processing internal transfer message")
    agc = await agcm.authorize()
    transactions = await agc.open_by_key(config.SHEET_ID.get_secret_value())
    aws = await transactions.worksheet('Транзакции')
    data = await parse_message(message)
    logger.debug(f"Parsed message data: {data}")
    last_row = await get_last_row(aws, 1)
    data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('сумма'), data.get('счёт откуда'),
                   data.get('счёт куда'), data.get('комментарий')]
    await add_record_to_table(aws, last_row, data_to_add, 1, 5)
    logger.info("Successfully processed internal transfer")


async def write_for_oborotka(message: str):
    logger.info("Processing oborotka message")
    agc = await agcm.authorize()
    oborotka = await agc.open_by_key(config.SHEET_ID.get_secret_value())
    aws = await oborotka.worksheet('Оборотка')
    data = await parse_message(message)
    tranz = await oborotka.worksheet('Транзакции')
    logger.debug(f"Parsed message data: {data}")
    last_row = await get_last_row(aws, 1)
    data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('сумма'), data.get('валюта'),
                   data.get('бенефициар'), data.get('комментарий')]
    await add_record_to_table(aws, last_row, data_to_add, 1, 5)
    # Часть Транзакций
    if '-' in data.get('сумма'):
        data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('сумма')[1:], data.get('счёт'),
                       'Внешний источник', 'оборотка']
    else:
        data_to_add = [datetime.now().strftime("%d.%m.%Y"), data.get('сумма'), 'Внешний источник',
                       data.get('счёт'), 'оборотка']
    await add_record_to_table(tranz, await get_last_row(tranz, 1), data_to_add, 1, 5)
    logger.info("Successfully processed oborotka")
