"""Qo'shimcha bepul tarjimonlar. Hammasi deep-translator bilan bir xil interfeysga ega:
Tarjimon(source='english', target='uzbek').translate('apple')
"""
from urllib.parse import quote

import requests

KODLAR = {'english': 'en', 'uzbek': 'uz'}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
TIMEOUT = 5


class TooManyRequests(Exception):
    """Server so'rovlar limitiga tushganda."""


class GoogleGtxTranslator:
    """Google'ning boshqa (translate.googleapis.com) manzili orqali tarjima."""

    URL = "https://translate.googleapis.com/translate_a/single"

    def __init__(self, source: str, target: str):
        self.src = KODLAR.get(source, source)
        self.dst = KODLAR.get(target, target)

    def translate(self, matn: str) -> str:
        r = requests.get(
            self.URL,
            params={'client': 'gtx', 'sl': self.src, 'tl': self.dst, 'dt': 't', 'q': matn},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if r.status_code == 429:
            raise TooManyRequests()
        r.raise_for_status()
        qismlar = [p[0] for p in r.json()[0] if p and p[0]]
        return ''.join(qismlar).strip()


class LingvaTranslator:
    """Lingva Translate ochiq serverlari orqali tarjima (kalitsiz)."""

    SERVERLAR = ("https://lingva.ml", "https://lingva.garudalinux.org")

    def __init__(self, source: str, target: str):
        self.src = KODLAR.get(source, source)
        self.dst = KODLAR.get(target, target)

    def translate(self, matn: str) -> str:
        oxirgi_xato = None
        for server in self.SERVERLAR:
            try:
                r = requests.get(
                    f"{server}/api/v1/{self.src}/{self.dst}/{quote(matn, safe='')}",
                    headers=HEADERS,
                    timeout=TIMEOUT,
                )
                if r.status_code == 429:
                    oxirgi_xato = TooManyRequests()
                    continue
                r.raise_for_status()
                natija = (r.json().get('translation') or '').strip()
                if natija:
                    return natija
            except Exception as xato:
                oxirgi_xato = xato
        raise oxirgi_xato or RuntimeError("Lingva javob bermadi")
