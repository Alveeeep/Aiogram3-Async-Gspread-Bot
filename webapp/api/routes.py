from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
import hashlib
import hmac
from urllib.parse import unquote
from loguru import logger
import sys

sys.path.append('/app')

from shared.utils.gsheets import (
    write_for_change_usdt,
    write_for_change_other,
    write_for_internal_transfer,
    write_for_oborotka
)

from shared.config import config

from webapp.schemas.forms import (
    USDTExchangeRequest,
    CurrencyExchangeRequest,
    InternalTransferRequest,
    OborotkaRequest,
    SuccessResponse,
    TransactionType,
    ExchangeType,
    OperationType, OptionsResponse, OptionItem
)

router = APIRouter(prefix="/api", tags=["transactions"])


def validate_telegram_webapp_data(init_data: str, bot_token: str) -> bool:
    """
    Проверка подлинности данных от Telegram WebApp
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        # Парсим данные
        parsed_data = dict(pair.split('=', 1) for pair in init_data.split('&'))

        # Извлекаем hash
        received_hash = parsed_data.pop('hash', None)
        if not received_hash:
            return False

        # Сортируем ключи и создаем строку для проверки
        data_check_string = '\n'.join(
            f"{k}={unquote(v)}"
            for k, v in sorted(parsed_data.items())
        )

        # Вычисляем hash
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        return calculated_hash == received_hash
    except Exception as e:
        logger.error(f"Error validating Telegram data: {e}")
        return False


async def verify_telegram_user(authorization: Optional[str] = Header(None)):
    """Middleware для проверки запросов от Telegram"""
    if not authorization:
        logger.warning("Missing Authorization header")
        return None

    if not validate_telegram_webapp_data(authorization, config.TOKEN.get_secret_value()):
        raise HTTPException(status_code=403, detail="Invalid Telegram data")

    return authorization


@router.post("/usdt-exchange", response_model=SuccessResponse)
async def submit_usdt_exchange(request: USDTExchangeRequest, authorization: Optional[str] = Header(None)):
    await verify_telegram_user(authorization)
    try:
        logger.info(f"Processing USDT exchange: {request.transaction_type}")

        message_parts = [
            f"Тип транзакции: Обмен",
            f"Тип: {request.transaction_type}",
            f"Сумма USDT: {request.usdt_amount}",
            f"Сумма в фиате: {request.fiat_amount}",
            f"Валюта: {request.currency}",
        ]

        if request.client_fio:
            message_parts.append(f"ФИО клиента: {request.client_fio}")
        if request.client_contact_info:
            message_parts.append(f"Контакт клиента: {request.client_contact_info}")

        if request.transaction_type == "Покупка USDT" and request.fiat_account:
            message_parts.append(f"Фиат счёт: {request.fiat_account}")

        message_parts.extend([
            f"Источник сделки: {request.source}",
            f"Из бота: {request.from_bot}",
            f"Менеджер: {request.manager}"
        ])

        message = "\n".join(message_parts)

        await write_for_change_usdt(message)

        logger.info("Successfully processed USDT exchange")
        return SuccessResponse(
            success=True,
            message="Данные успешно добавлены в таблицу"
        )
    except Exception as e:
        logger.error(f"Error in submit_usdt_exchange: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/currency-exchange", response_model=SuccessResponse)
async def submit_currency_exchange(request: CurrencyExchangeRequest, authorization: Optional[str] = Header(None)):
    await verify_telegram_user(authorization)
    try:
        logger.info(f"Processing currency exchange: {request.exchange_type}")

        message_parts = [
            f"Тип транзакции: Обмен",
            f"Тип: {request.exchange_type}",
        ]

        if request.client_fio:
            message_parts.append(f"ФИО клиента: {request.client_fio}")
        if request.client_contact_info:
            message_parts.append(f"Контакт клиента: {request.client_contact_info}")

        if request.exchange_type == "Покупка CHF за EUR":
            message_parts.extend([
                f"Сумма CHF: {request.chf_amount}",
                f"Сумма EUR: {request.eur_amount}",
            ])
        else:
            message_parts.extend([
                f"Сумма EUR: {request.eur_amount}",
                f"Сумма CHF: {request.chf_amount}",
            ])

        message_parts.extend([
            f"Счёт отправки: {request.from_account}",
            f"Счёт получения: {request.to_account}",
            f"Менеджер: {request.manager}",
            f"Из бота: {request.from_bot}"
        ])

        message = "\n".join(message_parts)

        await write_for_change_other(message)

        logger.info("Successfully processed currency exchange")
        return SuccessResponse(
            success=True,
            message="Данные успешно добавлены в таблицу"
        )
    except Exception as e:
        logger.error(f"Error in submit_currency_exchange: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/internal-transfer", response_model=SuccessResponse)
async def submit_internal_transfer(request: InternalTransferRequest, authorization: Optional[str] = Header(None)):
    await verify_telegram_user(authorization)
    try:
        logger.info("Processing internal transfer")

        message_parts = [
            f"Тип транзакции: Внутренний перевод",
            f"Сумма: {request.amount}",
            f"Счёт откуда: {request.from_account}",
            f"Счёт куда: {request.to_account}",
            f"Комментарий: {request.comment}"
        ]

        message = "\n".join(message_parts)

        await write_for_internal_transfer(message)

        logger.info("Successfully processed internal transfer")
        return SuccessResponse(
            success=True,
            message="Данные успешно добавлены в таблицу"
        )
    except Exception as e:
        logger.error(f"Error in submit_internal_transfer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oborotka", response_model=SuccessResponse)
async def submit_oborotka(request: OborotkaRequest, authorization: Optional[str] = Header(None)):
    await verify_telegram_user(authorization)
    try:
        logger.info(f"Processing oborotka: {request.operation_type}")

        final_amount = f"-{request.amount}" if request.operation_type == "Списание" else request.amount

        message_parts = [
            f"Тип транзакции: Действие с обороткой",
            f"Сумма: {final_amount}",
            f"Валюта: {request.currency}",
            f"Счёт: {request.account}",
            f"Бенефициар: {request.beneficiary}",
            f"Комментарий: {request.comment}"
        ]

        message = "\n".join(message_parts)

        await write_for_oborotka(message)

        logger.info("Successfully processed oborotka")
        return SuccessResponse(
            success=True,
            message="Данные успешно добавлены в таблицу"
        )
    except Exception as e:
        logger.error(f"Error in submit_oborotka: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options", response_model=OptionsResponse)
async def get_options(authorization: Optional[str] = Header(None)):
    """
    Возвращает справочники для выпадающих списков в Mini App.
    Требует валидный initData в заголовке Authorization.
    """
    await verify_telegram_user(authorization)

    # 💡 Здесь можно подключить БД или кэш вместо хардкода
    options = OptionsResponse(
        sources=[
            OptionItem(id="binance", name="Binance"),
            OptionItem(id="bybit", name="Bybit"),
            OptionItem(id="okx", name="OKX"),
            OptionItem(id="manual", name="Вручную"),
        ],
        bots=[
            OptionItem(id="none", name="Нет"),
            OptionItem(id="bot", name="Бот")
        ],
        managers=[
            OptionItem(id="alexey", name="Алексей"),
            OptionItem(id="maria", name="Мария"),
            OptionItem(id="ivan", name="Иван"),
            OptionItem(id="anastasia", name="Анастасия"),
        ]
    )

    logger.info("Returning options for Mini App")
    return options
