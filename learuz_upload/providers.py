from urllib.parse import quote
import requests
from deep_translator import GoogleTranslator, MyMemoryTranslator

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
TIMEOUT = 5

class TooManyRequests(Exception):
    """So'rovlar limiti oshganda."""
    pass

class GoogleGtxTranslator:
    """Google gtx orqali to'g'ridan-to'g'ri so'rov"""
    def __init__(self, source: str, target: str):
        self.source = 'en' if 'eng' in source.lower() else 'uz'
        self.target = 'uz' if 'uz' in target.lower() else 'en'

    def translate(self, matn: str) -> str:
        url = "https://translate.googleapis.com/translate_a/single"
        r = requests.get(
            url,
            params={'client': 'gtx', 'sl': self.source, 'tl': self.target, 'dt': 't', 'q': matn},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if r.status_code == 429:
            raise TooManyRequests("Limit")
        r.raise_for_status()
        qismlar = [p[0] for p in r.json()[0] if p and p[0]]
        return ''.join(qismlar).strip()

class LingvaTranslator:
    """Lingva Translate ochiq serverlari orqali tarjima (o'zbek tilini qo'llab-quvvatlaydi)"""
    SERVERLAR = ("https://lingva.ml", "https://lingva.garudalinux.org")

    def __init__(self, source: str, target: str):
        self.source = 'en' if 'eng' in source.lower() else 'uz'
        self.target = 'uz' if 'uz' in target.lower() else 'en'

    def translate(self, matn: str) -> str:
        for server in self.SERVERLAR:
            try:
                r = requests.get(
                    f"{server}/api/v1/{self.source}/{self.target}/{quote(matn, safe='')}",
                    headers=HEADERS,
                    timeout=TIMEOUT,
                )
                if r.status_code == 429:
                    continue
                if r.status_code == 200:
                    natija = (r.json().get('translation') or '').strip()
                    if natija:
                        return natija
            except Exception:
                continue
        raise Exception("Lingva serverlari ishlamadi")
