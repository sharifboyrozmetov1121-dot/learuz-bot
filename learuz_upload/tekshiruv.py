"""Tarjimonlarni alohida-alohida tekshiradi: qaysi biri ishlayapti, qaysi biri osilib qolyapti."""
import threading
import time

from logic import TARJIMONLAR, tarjima_qil

KUTISH = 12  # soniya


def toza(matn):
    """Konsol emoji'larni chiqara olmasa xato bermasligi uchun."""
    return str(matn).encode('ascii', 'replace').decode()


def sinov(nom, funksiya):
    natija = {}

    def ish():
        try:
            natija['qiymat'] = funksiya()
        except Exception as xato:
            natija['xato'] = f"{type(xato).__name__}: {xato}"

    boshlandi = time.time()
    oqim = threading.Thread(target=ish, daemon=True)
    oqim.start()
    oqim.join(timeout=KUTISH)
    sekund = round(time.time() - boshlandi, 1)

    if oqim.is_alive():
        print(f"XATO  {nom}: {KUTISH} soniyada javob bermadi (osilib qoldi)")
    elif 'xato' in natija:
        print(f"XATO  {nom}: {toza(natija['xato'])[:150]} ({sekund} s)")
    else:
        print(f"OK    {nom}: {toza(natija['qiymat'])} ({sekund} s)")


print("Tarjimonlar tekshirilmoqda (book -> uzbek)...\n")
for dvigatel in TARJIMONLAR:
    sinov(dvigatel.__name__, lambda d=dvigatel: d(source='english', target='uzbek').translate('book'))

print()
sinov("Botning to'liq tarjimasi", lambda: tarjima_qil('book').javob)
print("\nTekshiruv tugadi.")
