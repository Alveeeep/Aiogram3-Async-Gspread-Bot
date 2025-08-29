import re
import asyncio


async def parse_message(message):
    # Разделяем сообщение на блоки по пустым строкам
    blocks = re.split(r'\n\s*\n', message.strip())
    data = {}

    for block in blocks:
        lines = block.strip().splitlines()
        for line in lines:
            # Ищем строки вида "Ключ: Значение"
            match = re.match(r'^(.*?):\s*(.*)$', line)
            if match:
                key, value = match.groups()
                key = key.strip().lower()
                value = value.strip()
                # Можно дополнительно нормализовать ключи
                data[key] = value
    return data
