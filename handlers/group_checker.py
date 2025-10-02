from aiogram import Router, F
from aiogram.types import Message
from utils.gsheets import write_for_change_usdt, write_for_oborotka, write_for_change_other, write_for_internal_transfer
from loguru import logger

router = Router()


@router.message(F.text.contains("Тип транзакции: Обмен") & (F.text.contains("USDT") | F.text.contains("usdt")))
async def message_one(message: Message):
    try:
        logger.info(f"Processing USDT exchange message from {message.from_user.id}")
        await write_for_change_usdt(message.text)
        logger.info(f"Successfully processed message from {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error processing message from {message.from_user.id}: {e}")
        await message.answer(f"❌Ошибка: {e}")


@router.message(F.text.contains("Тип транзакции: Обмен") & (
        F.text.contains("Покупка CHF") | F.text.contains("Покупка EUR")))
async def message_two(message: Message):
    try:
        logger.info(f"Processing currency exchange message from {message.from_user.id}")
        await write_for_change_other(message.text)
        logger.info(f"Successfully processed message from {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error processing message from {message.from_user.id}: {e}")
        await message.answer(f"❌Ошибка: {e}")


@router.message(F.text.contains("Тип транзакции: Внутрен"))
async def message_three(message: Message):
    try:
        logger.info(f"Processing internal transfer message from {message.from_user.id}")
        await write_for_internal_transfer(message.text)
        logger.info(f"Successfully processed message from {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error processing message from {message.from_user.id}: {e}")
        await message.answer(f"❌Ошибка: {e}")


@router.message(F.text.contains("Тип транзакции: Действие с обороткой"))
async def message_four(message: Message):
    try:
        logger.info(f"Processing оборотка message from {message.from_user.id}")
        await write_for_oborotka(message.text)
        logger.info(f"Successfully processed message from {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error processing message from {message.from_user.id}: {e}")
        await message.answer(f"❌Ошибка: {e}")
