"""Server qismi: sog'liqni tekshirish manzili va webhook yo'li."""
import hashlib

from aiohttp import web


def webhook_yoli(token: str) -> str:
    """Webhook manzili tokendan olingan sirli qism bilan (boshqalar taxmin qila olmasin)."""
    return "/webhook/" + hashlib.sha256(token.encode()).hexdigest()[:32]


async def salomatlik(request):
    """Bot tirikligini tekshirish uchun (UptimeRobot kabi xizmatlar shu manzilga so'rov yuboradi)."""
    return web.Response(text="OK")


def ilova_yasash() -> web.Application:
    app = web.Application()
    app.router.add_get('/', salomatlik)
    return app
