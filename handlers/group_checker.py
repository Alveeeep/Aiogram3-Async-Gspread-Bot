from aiogram import Router, F
from aiogram.types import Message
from utils.gsheets import write_for_change_usdt, write_for_oborotka, write_for_change_other, write_for_internal_transfer

router = Router()


@router.message(F.text.contains("Тип транзакции: Обмен") & (F.text.contains("usdt") | F.text.contains("USDT")))
async def message_one(message: Message):
    try:
        await write_for_change_usdt(message.text)
    except Exception as e:
        await message.answer(f"❌Ошибка: {e}")


@router.message(F.text.contains("Тип транзакции: Обмен") & (
        F.text.contains("Покупка CHF") | F.text.contains("Покупка EUR") | F.text.contains("Покупка USD")))
async def message_two(message: Message):
    try:
        await write_for_change_other(message.text)
    except Exception as e:
        await message.answer(f"❌Ошибка: {e}")


@router.message(F.text.contains("Тип транзакции: Внутренний перевод"))
async def message_three(message: Message):
    try:
        await write_for_internal_transfer(message.text)
    except Exception as e:
        await message.answer(f"❌Ошибка: {e}")


@router.message(F.text.contains("Тип транзакции: Действие с обороткой"))
async def message_four(message: Message):
    try:
        await write_for_oborotka(message.text)
    except Exception as e:
        await message.answer(f"❌Ошибка: {e}")
