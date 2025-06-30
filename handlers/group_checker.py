from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text.contains("Тип транзакции: Обмен") & F.text.contains("usdt"))
async def message_one(message: Message):
    await message.answer("Это текстовое сообщение!")


@router.message(F.text.contains("Тип транзакции: Обмен") & (
        F.text.contains("Покупка CHF") | F.text.contains("Покупка EUR") | F.text.contains("Покупка USD")))
async def message_two(message: Message):
    await message.answer("Это текстовое сообщение!")


@router.message(F.text.contains("Тип транзакции: Внутренний перевод"))
async def message_three(message: Message):
    await message.answer("Это текстовое сообщение!")


@router.message(F.text.contains("Тип транзакции: Действие с обороткой"))
async def message_four(message: Message):
    await message.answer("Это текстовое сообщение!")
