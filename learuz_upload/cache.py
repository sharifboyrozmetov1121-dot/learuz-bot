"""Tarjimalar keshi (SQLite). Bir marta tarjima qilingan so'z qayta so'ralmaydi.

Kesh hech qachon botni to'xtatmasligi kerak: baza bilan xato bo'lsa, shunchaki
kesh ishlamaganday davom etiladi.
"""
import logging
import os
import sqlite3
import threading
import time

# Baza fayli: standart holda bot papkasidagi cache.db (.env da CACHE_DB bilan o'zgartirish mumkin)
DB_YOLI = os.getenv("CACHE_DB") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.db")

_qulf = threading.RLock()
_ulanish = None


def ochish(yol: str = None):
    """Bazani ochadi (yo'q bo'lsa yaratadi). Testlarda ':memory:' berish mumkin."""
    global _ulanish
    with _qulf:
        if _ulanish is not None:
            _ulanish.close()
        _ulanish = sqlite3.connect(yol or DB_YOLI, check_same_thread=False)
        _ulanish.execute(
            "CREATE TABLE IF NOT EXISTS tarjimalar ("
            "yonalish TEXT NOT NULL, manba TEXT NOT NULL, natija TEXT NOT NULL, "
            "yaratilgan INTEGER NOT NULL, PRIMARY KEY (yonalish, manba))"
        )
        _ulanish.commit()


def yopish():
    global _ulanish
    with _qulf:
        if _ulanish is not None:
            _ulanish.close()
            _ulanish = None


def _baza():
    if _ulanish is None:
        ochish()
    return _ulanish


def ol(yonalish: str, manba: str):
    """Saqlangan tarjimani qaytaradi, yo'q bo'lsa (yoki xato bo'lsa) None."""
    try:
        with _qulf:
            qator = _baza().execute(
                "SELECT natija FROM tarjimalar WHERE yonalish = ? AND manba = ?",
                (yonalish, manba),
            ).fetchone()
        return qator[0] if qator else None
    except Exception:
        logging.warning("Keshdan o'qib bo'lmadi", exc_info=True)
        return None


def saqla(yonalish: str, manba: str, natija: str):
    """Tarjimani saqlaydi (borini yangilaydi). Xato bo'lsa jim o'tadi."""
    try:
        with _qulf:
            baza = _baza()
            baza.execute(
                "INSERT OR REPLACE INTO tarjimalar (yonalish, manba, natija, yaratilgan) "
                "VALUES (?, ?, ?, ?)",
                (yonalish, manba, natija, int(time.time())),
            )
            baza.commit()
    except Exception:
        logging.warning("Keshga yozib bo'lmadi", exc_info=True)


def soni() -> int:
    """Keshdagi tarjimalar soni."""
    try:
        with _qulf:
            return _baza().execute("SELECT COUNT(*) FROM tarjimalar").fetchone()[0]
    except Exception:
        return 0
