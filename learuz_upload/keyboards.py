from aiogram import types

from logic import YONALISHLAR

# Telegram callback_data 64 baytdan oshmasligi kerak
CALLBACK_LIMIT = 64


def yonalish_klaviaturasi(joriy: str) -> types.InlineKeyboardMarkup:
    """Yo'nalish tanlash tugmalari (tanlangani ✅ bilan belgilanadi)."""
    kb = types.InlineKeyboardMarkup(row_width=1)
    for kod, y in YONALISHLAR.items():
        belgi = "✅ " if kod == joriy else ""
        kb.add(types.InlineKeyboardButton(belgi + y['nom'], callback_data=f"dir:{kod}"))
    return kb


def natija_klaviaturasi(soz: str = None, til: str = 'en') -> types.InlineKeyboardMarkup:
    """Tarjima ostidagi tugmalar: 🔊 Talaffuz (faqat inglizcha natijada) va yo'nalishni almashtirish."""
    kb = types.InlineKeyboardMarkup(row_width=1)

    if soz and til == 'en':
        data = f"tts:{til}:{soz}"
        if len(data.encode('utf-8')) <= CALLBACK_LIMIT:
            kb.add(types.InlineKeyboardButton("🔊 Talaffuz", callback_data=data))

    kb.add(types.InlineKeyboardButton("🔄 Yo'nalishni almashtirish", callback_data="dir:toggle"))
    return kb
