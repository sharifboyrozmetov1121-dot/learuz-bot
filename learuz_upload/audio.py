from io import BytesIO

from gtts import gTTS

# gTTS da o'zbek tili yo'q. O'zbek lotin yozuvi turkchaga yaqin, shuning uchun
# o'zbekcha so'zlar turkcha ovozda o'qiladi (harflari moslashtiriladi).
GTTS_TIL = {'en': 'en', 'uz': 'tr'}

APOSTROFLAR = str.maketrans({'ʻ': "'", '’': "'", '‘': "'", '`': "'", 'ʼ': "'"})
UZ_TURK = (("o'", 'o'), ("g'", 'ğ'), ('sh', 'ş'), ('ch', 'ç'), ('j', 'c'), ('x', 'h'), ('q', 'k'))


def uzbek_matnini_turkchaga(soz: str) -> str:
    """O'zbekcha so'zni turkcha ovoz to'g'ri o'qiydigan yozuvga moslashtiradi."""
    soz = soz.lower().translate(APOSTROFLAR)
    for eski, yangi in UZ_TURK:
        soz = soz.replace(eski, yangi)
    return soz.replace("'", "")


def talaffuz_yarat(soz: str, til: str = 'en') -> BytesIO:
    """So'zning mp3 talaffuzini xotirada yaratadi (diskka yozmaydi).

    til: 'en' (inglizcha) yoki 'uz' (o'zbekcha).
    """
    matn = uzbek_matnini_turkchaga(soz) if til == 'uz' else soz
    buf = BytesIO()
    gTTS(text=matn, lang=GTTS_TIL.get(til, 'en')).write_to_fp(buf)
    buf.seek(0)
    return buf
