from deep_translator import GoogleTranslator, MyMemoryTranslator, PonsTranslator

class GoogleGtxTranslator:
    """Google gtx orqali tarjima"""
    def __init__(self, source: str, target: str):
        self.source = 'en' if 'eng' in source.lower() else 'uz'
        self.target = 'uz' if 'uz' in target.lower() else 'en'

    def translate(self, matn: str) -> str:
        # To'g'ridan-to'g'ri deep-translator ning GoogleTranslator'idan foydalanamiz
        res = GoogleTranslator(source=self.source, target=self.target).translate(matn)
        if not res:
            raise Exception("Bo'sh javob")
        return res

class LingvaTranslator:
    """Lingva o'rniga PonsTranslator (limitga chidamliroq)"""
    def __init__(self, source: str, target: str):
        self.source = 'en' if 'eng' in source.lower() else 'uz'
        self.target = 'uz' if 'uz' in target.lower() else 'en'

    def translate(self, matn: str) -> str:
        # Pons lug'ati orqali tarjima qilish
        res = PonsTranslator(source=self.source, target=self.target).translate(matn)
        if not res:
            raise Exception("Bo'sh javob")
        return res
