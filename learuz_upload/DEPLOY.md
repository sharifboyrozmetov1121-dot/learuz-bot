# Botni Render.com ga joylash (bepul, kartasiz)

Natija: kompyuteringiz o'chiq bo'lsa ham bot ishlaydi.

## 1. GitHub ga yuklash
1. github.com da ro'yxatdan o'ting.
2. New repository -> nomi: learuz-bot -> **Private** -> Create.
3. "uploading an existing file" ni bosing va papkadagi fayllarni tashlang.
   **MUHIM: `.env` faylini va `cache.db` ni YUKLAMANG** (ichida bot tokeni bor).
4. Commit changes.

## 2. Render da xizmat yaratish
1. render.com -> GitHub orqali kiring.
2. New -> Web Service -> learuz-bot repozitoriyasini tanlang.
3. Sozlamalar:
   - Language: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
   - Instance Type: **Free**
4. Environment Variables (Add):
   - `BOT_TOKEN` = BotFather bergan token
   - `PYTHON_VERSION` = 3.11.9
   - `CACHE_DB` = /tmp/cache.db
5. Create Web Service. Build tugashini kuting (bir necha daqiqa).

## 3. Uxlab qolmasligi uchun
Render bepul xizmati 15 daqiqa so'rovsiz qolsa uxlaydi (qayta uyg'onishi ~1 daqiqa).
1. uptimerobot.com da bepul ro'yxatdan o'ting.
2. New monitor -> HTTP(s) -> URL: `https://SIZNING-NOM.onrender.com/` -> interval 5 daqiqa.

## 4. Tekshirish
- Brauzerda `https://SIZNING-NOM.onrender.com/` ochsangiz, `OK` chiqishi kerak.
- Telegramda botga so'z yozing.

## Eslatma
- Server ishlayotganda kompyuterda `bot.py` ni ishga tushirmang: polling rejimi webhookni o'chirib qo'yadi.
- Xizmat qayta ishga tushsa, kesh va tanlangan yo'nalish tozalanadi (bu normal).
