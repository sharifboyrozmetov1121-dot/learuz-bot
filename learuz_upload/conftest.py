import pytest

import cache


@pytest.fixture(autouse=True)
def toza_kesh():
    """Har bir test uchun alohida, bo'sh xotiradagi kesh (haqiqiy cache.db ga tegmaydi)."""
    cache.ochish(":memory:")
    yield
    cache.yopish()
