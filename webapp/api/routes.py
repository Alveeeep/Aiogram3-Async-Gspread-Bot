from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from loguru import logger
import sys

sys.path.append('/app')

from shared.utils.gsheets import (
    write_for_change_usdt,
    write_for_change_other,
    write_for_internal_transfer,
    write_for_oborotka
)

from webapp.schemas.forms import (
    USDTExchangeRequest,
    CurrencyExchangeRequest,
    InternalTransferRequest,
    OborotkaRequest,
    SuccessResponse,
    TransactionType,
    ExchangeType,
    OperationType
)

router = APIRouter(prefix="/api", tags=["transactions"])


@router.post("/usdt-exchange", response_model=SuccessResponse)
async def submit_usdt_exchange(request: USDTExchangeRequest):
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
async def submit_currency_exchange(request: CurrencyExchangeRequest):
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
async def submit_internal_transfer(request: InternalTransferRequest):
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
async def submit_oborotka(request: OborotkaRequest):
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
