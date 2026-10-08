import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import MessageNotModified
from dotenv import load_dotenv

from audio import talaffuz_yarat
from keyboards import natija_klaviaturasi, yonalish_klaviaturasi
from logic import DEFAULT_YONALISH, YONALISHLAR, tarjima_qil
from server import ilova_yasash, webhook_yoli

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise SystemExit(".env faylida BOT_TOKEN topilmadi. .env.example ni ko'ring.")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Foydalanuvchi tanlagan yo'nalish (keyingi bosqichda bazaga o'tkazamiz)
foydalanuvchi_yonalishi = {}


def tayyor_xabar(kod: str) -> str:
    return (
        f"✅ Yo'nalish tanlandi:\n{YONALISHLAR[kod]['nom']}\n\n"
        "Marhamat, so'zni yuborishingiz mumkin. ✍️"
    )


def yonalish_ol(user_id: int) -> str:
    return foydalanuvchi_yonalishi.get(user_id, DEFAULT_YONALISH)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    ism = message.from_user.first_name
    await message.answer(
        f"Salom, {ism}! 👋\n\n"
        "Men inglizcha-o'zbekcha tarjimon botman.\n"
        "Tarjima yo'nalishini tanlang va so'z yuboring:",
        reply_markup=yonalish_klaviaturasi(yonalish_ol(message.from_user.id)),
    )


@dp.message_handler(commands=['yonalish'])
async def yonalish_menyu(message: types.Message):
    await message.answer(
        "Tarjima yo'nalishini tanlang:",
        reply_markup=yonalish_klaviaturasi(yonalish_ol(message.from_user.id)),
    )


@dp.message_handler(commands=['help'])
async def yordam(message: types.Message):
    await message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "• So'z yoki qisqa gap yuboring, men tarjima qilaman.\n"
        "• /yonalish — tarjima yo'nalishini tanlash\n"
        "• /start — botni qayta boshlash",
        parse_mode=types.ParseMode.HTML,
    )


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('dir:'))
async def yonalish_tanlandi(call: types.CallbackQuery):
    kod = call.data.split(':', 1)[1]
    user_id = call.from_user.id

    if kod == 'toggle':
        kod = 'uz_en' if yonalish_ol(user_id) == 'en_uz' else 'en_uz'
        foydalanuvchi_yonalishi[user_id] = kod
        await call.answer()
        await call.message.answer(tayyor_xabar(kod))
        return

    if kod not in YONALISHLAR:
        await call.answer()
        return

    foydalanuvchi_yonalishi[user_id] = kod
    await call.answer(f"Tanlandi: {YONALISHLAR[kod]['nom']}")
    try:
        await call.message.edit_reply_markup(reply_markup=yonalish_klaviaturasi(kod))
    except MessageNotModified:
        pass
    await call.message.answer(tayyor_xabar(kod))


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('tts:'))
async def talaffuz(call: types.CallbackQuery):
    try:
        _, til, soz = call.data.split(':', 2)
    except ValueError:
        await call.answer()
        return
    soz = soz.strip()

    # Bo'sh yoki juda uzun matnni o'qimaymiz
    if til != 'en' or not soz or len(soz) > 50 or not any(ch.isalpha() for ch in soz):
        await call.answer("Bu so'zni o'qib bo'lmaydi", show_alert=True)
        return

    await call.answer("🔊 Tayyorlanmoqda...")
    loop = asyncio.get_running_loop()
    try:
        audio = await loop.run_in_executor(None, talaffuz_yarat, soz, til)
    except Exception:
        logging.exception("Talaffuz yaratishda xatolik")
        await call.message.answer("Talaffuzni yaratib bo'lmadi. Birozdan keyin qayta urinib ko'ring.")
        return

    await bot.send_audio(
        call.message.chat.id,
        types.InputFile(audio, filename=f"{soz}.mp3"),
        title=soz,
        performer="LearUz Bot",
    )


@dp.message_handler()
async def tarjima(message: types.Message):
    await bot.send_chat_action(message.chat.id, types.ChatActions.TYPING)
    yonalish = yonalish_ol(message.from_user.id)

    # Tarjima internetga murojaat qiladi, shuning uchun botni to'xtatmaslik uchun alohida oqimda
    loop = asyncio.get_running_loop()
    n = await loop.run_in_executor(None, tarjima_qil, message.text, yonalish)

    await message.answer(
        n.javob,
        reply_markup=natija_klaviaturasi(n.talaffuz_soz, n.talaffuz_tili or 'en'),
    )


# Serverda (masalan, Render) webhook rejimida ishlaydi, kompyuterda esa polling rejimida.
# Server manzili WEBHOOK_URL yoki Render bergan RENDER_EXTERNAL_URL o'zgaruvchisidan olinadi.
WEBHOOK_BASE = os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL")
PORT = int(os.getenv("PORT", "10000"))


async def komandalar_ornat(dispatcher: Dispatcher):
    await dispatcher.bot.set_my_commands([
        types.BotCommand("start", "Botni boshlash"),
        types.BotCommand("yonalish", "Tarjima yo'nalishini tanlash"),
        types.BotCommand("help", "Yordam"),
    ])


async def on_startup_polling(dispatcher: Dispatcher):
    # Polling ishlashi uchun eski webhook o'chiriladi
    await dispatcher.bot.delete_webhook()
    await komandalar_ornat(dispatcher)


async def on_startup_webhook(dispatcher: Dispatcher):
    await dispatcher.bot.set_webhook(WEBHOOK_BASE.rstrip('/') + webhook_yoli(API_TOKEN))
    await komandalar_ornat(dispatcher)


def webhook_rejimi():
    ijrochi = executor.Executor(dp)
    ijrochi.on_startup(on_startup_webhook, polling=False)
    ijrochi.set_webhook(webhook_path=webhook_yoli(API_TOKEN), web_app=ilova_yasash())
    ijrochi.run_app(host='0.0.0.0', port=PORT)


if __name__ == '__main__':
    if WEBHOOK_BASE:
        logging.info("Webhook rejimi: %s", WEBHOOK_BASE)
        webhook_rejimi()
    else:
        logging.info("Polling rejimi (kompyuterda)")
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup_polling)
