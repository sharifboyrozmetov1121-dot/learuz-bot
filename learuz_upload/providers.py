from deep_translator import GoogleTranslator

class GoogleGtxTranslator:
    """Eski nomlar xato bermasligi uchun saqlab qolingan klass"""
    def __init__(self, source: str, target: str):
        self.source = 'en' if 'eng' in source.lower() else 'uz'
        self.target = 'uz' if 'uz' in target.lower() else 'en'

    def translate(self, matn: str) -> str:
        try:
            res = GoogleTranslator(source=self.source, target=self.target).translate(matn)
            return res if res else matn
        except Exception as e:
            print(f"Tarjima xatosi: {e}")
            raise e

class LingvaTranslator:
    """Eski Lingva o'rniga ham deep-translator ishlaydigan klass"""
    def __init__(self, source: str, target: str):
        self.source = 'en' if 'eng' in source.lower() else 'uz'
        self.target = 'uz' if 'uz' in target.lower() else 'en'

    def translate(self, matn: str) -> str:
        try:
            res = GoogleTranslator(source=self.source, target=self.target).translate(matn)
            return res if res else matn
        except Exception as e:
            print(f"Tarjima xatosi: {e}")
            raise e
