import requests

class GoogleGtxTranslator:
    def __init__(self, source: str, target: str):
        self.source = 'en' if 'eng' in source.lower() else 'uz'
        self.target = 'uz' if 'uz' in target.lower() else 'en'

    def translate(self, matn: str) -> str:
        url = "https://translate.googleapis.com/translate_a/single"
        r = requests.get(
            url,
            params={'client': 'gtx', 'sl': self.source, 'tl': self.target, 'dt': 't', 'q': matn},
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5,
        )
        if r.status_code == 200:
            qismlar = [p[0] for p in r.json()[0] if p and p[0]]
            return ''.join(qismlar).strip()
        raise Exception("Tarjima xatosi")

class LingvaTranslator:
    def __init__(self, source: str, target: str):
        self.source = 'en' if 'eng' in source.lower() else 'uz'
        self.target = 'uz' if 'uz' in target.lower() else 'en'

    def translate(self, matn: str) -> str:
        r = requests.get(
            f"https://lingva.ml/api/v1/{self.source}/{self.target}/{matn}",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5,
        )
        if r.status_code == 200:
            return r.json().get('translation', '')
        raise Exception("Lingva xatosi")
