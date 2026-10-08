import asyncio

from aiohttp.test_utils import TestClient, TestServer

from server import ilova_yasash, webhook_yoli


def test_salomatlik_manzili_ishlaydi():
    async def sinov():
        async with TestClient(TestServer(ilova_yasash())) as mijoz:
            javob = await mijoz.get('/')
            assert javob.status == 200
            assert await javob.text() == "OK"
            assert (await mijoz.head('/')).status == 200  # uptime xizmatlari HEAD ham yuboradi

    asyncio.run(sinov())


def test_webhook_yoli_tokenni_oshkor_qilmaydi():
    yol = webhook_yoli("123456:ABC-DEF")
    assert yol.startswith("/webhook/")
    assert "123456" not in yol and "ABC" not in yol


def test_webhook_yoli_doimiy_va_tokenga_bogliq():
    assert webhook_yoli("a:b") == webhook_yoli("a:b")
    assert webhook_yoli("a:b") != webhook_yoli("a:c")
