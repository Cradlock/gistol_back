from async_lru import alru_cache

# Кэшируем результат сетевого запроса к JWKS Телеграма
@alru_cache(ttl=86400) # Кэш на 24 часа
async def fetch_telegram_jwks(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
