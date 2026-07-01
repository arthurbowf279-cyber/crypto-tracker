"""
Crypto Portfolio Tracker
========================
FastAPI-сервис для отслеживания крипто-портфолио.
Цены берутся с CoinGecko API (бесплатно, без ключа).

Запуск:
    pip install -r requirements.txt
    uvicorn main:app --reload

Документация: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx
from typing import Optional

app = FastAPI(
    title="Crypto Portfolio Tracker",
    description="Отслеживай свой крипто-портфель в реальном времени",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CoinGecko API — бесплатный источник цен без регистрации
# Лимит: ~30 запросов/мин для бесплатного тарифа
# ---------------------------------------------------------------------------
COINGECKO_URL = "https://api.coingecko.com/api/v3"

# Словарь для перевода тикера в ID CoinGecko
# Полный список: https://api.coingecko.com/api/v3/coins/list
TICKER_TO_ID: dict[str, str] = {
    "btc":  "bitcoin",
    "eth":  "ethereum",
    "sol":  "solana",
    "bnb":  "binancecoin",
    "xrp":  "ripple",
    "ada":  "cardano",
    "doge": "dogecoin",
    "ton":  "the-open-network",
    "avax": "avalanche-2",
    "dot":  "polkadot",
}

# ---------------------------------------------------------------------------
# "База данных" в памяти (в продакшене — PostgreSQL)
# Структура: { "btc": 0.5, "eth": 2.0, ... }
# ---------------------------------------------------------------------------
portfolio: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Схемы
# ---------------------------------------------------------------------------

class AddAssetRequest(BaseModel):
    """Добавить монету в портфолио."""
    ticker: str = Field(..., example="btc", description="Тикер монеты (btc, eth, sol...)")
    amount: float = Field(..., gt=0, example=0.5, description="Количество монет")


class AssetInfo(BaseModel):
    """Информация об одной монете в портфолио."""
    ticker: str
    amount: float
    price_usd: float
    value_usd: float
    change_24h_pct: Optional[float]  # изменение цены за 24 часа в %


class PortfolioResponse(BaseModel):
    """Полный отчёт по портфолио."""
    assets: list[AssetInfo]
    total_value_usd: float


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

async def fetch_prices(coin_ids: list[str]) -> dict:
    """
    Запрашивает актуальные цены у CoinGecko.
    Возвращает словарь: { "bitcoin": {"usd": 65000, "usd_24h_change": 2.5}, ... }
    """
    ids_param = ",".join(coin_ids)
    url = f"{COINGECKO_URL}/simple/price"
    params = {
        "ids": ids_param,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Не удалось получить цены от CoinGecko. Попробуйте позже."
        )

    return response.json()


# ---------------------------------------------------------------------------
# Эндпоинты
# ---------------------------------------------------------------------------

@app.get("/coins", summary="Список поддерживаемых монет")
async def list_coins() -> dict:
    """Показывает все монеты, которые поддерживает трекер."""
    return {
        "supported_coins": [
            {"ticker": ticker, "name": coin_id}
            for ticker, coin_id in TICKER_TO_ID.items()
        ]
    }


@app.post("/portfolio/add", summary="Добавить монету в портфолио")
async def add_asset(request: AddAssetRequest) -> dict:
    """
    Добавляет монету в портфолио или увеличивает существующую позицию.
    Пример: { "ticker": "btc", "amount": 0.5 }
    """
    ticker = request.ticker.lower()

    # Проверяем, поддерживается ли монета
    if ticker not in TICKER_TO_ID:
        raise HTTPException(
            status_code=400,
            detail=f"Монета '{ticker}' не поддерживается. Доступны: {list(TICKER_TO_ID.keys())}"
        )

    # Добавляем к существующей позиции (или создаём новую)
    portfolio[ticker] = portfolio.get(ticker, 0) + request.amount

    return {
        "status": "ok",
        "ticker": ticker,
        "total_amount": portfolio[ticker],
        "message": f"Добавлено {request.amount} {ticker.upper()}. Итого: {portfolio[ticker]}"
    }


@app.delete("/portfolio/remove/{ticker}", summary="Удалить монету из портфолио")
async def remove_asset(ticker: str) -> dict:
    """Полностью убирает монету из портфолио."""
    ticker = ticker.lower()

    if ticker not in portfolio:
        raise HTTPException(status_code=404, detail=f"Монеты {ticker} нет в портфолио")

    del portfolio[ticker]
    return {"status": "ok", "message": f"{ticker.upper()} удалён из портфолио"}


@app.get("/portfolio", summary="Текущий портфолио с ценами")
async def get_portfolio() -> PortfolioResponse:
    """
    Возвращает весь портфолио с актуальными ценами и общей стоимостью.
    Цены подтягиваются с CoinGecko в реальном времени.
    """
    if not portfolio:
        return PortfolioResponse(assets=[], total_value_usd=0)

    # Получаем ID монет для запроса к API
    coin_ids = [TICKER_TO_ID[ticker] for ticker in portfolio]

    # Запрашиваем актуальные цены
    prices_data = await fetch_prices(coin_ids)

    assets = []
    total_value = 0.0

    for ticker, amount in portfolio.items():
        coin_id = TICKER_TO_ID[ticker]
        coin_data = prices_data.get(coin_id, {})

        price_usd = coin_data.get("usd", 0)
        change_24h = coin_data.get("usd_24h_change")
        value_usd = price_usd * amount
        total_value += value_usd

        assets.append(AssetInfo(
            ticker=ticker.upper(),
            amount=amount,
            price_usd=round(price_usd, 2),
            value_usd=round(value_usd, 2),
            change_24h_pct=round(change_24h, 2) if change_24h else None,
        ))

    # Сортируем по стоимости — самые крупные позиции сверху
    assets.sort(key=lambda x: x.value_usd, reverse=True)

    return PortfolioResponse(
        assets=assets,
        total_value_usd=round(total_value, 2),
    )


@app.get("/price/{ticker}", summary="Цена конкретной монеты")
async def get_price(ticker: str) -> dict:
    """Быстрая проверка цены одной монеты."""
    ticker = ticker.lower()

    if ticker not in TICKER_TO_ID:
        raise HTTPException(
            status_code=400,
            detail=f"Монета '{ticker}' не поддерживается"
        )

    coin_id = TICKER_TO_ID[ticker]
    prices_data = await fetch_prices([coin_id])
    coin_data = prices_data.get(coin_id, {})

    return {
        "ticker": ticker.upper(),
        "price_usd": coin_data.get("usd"),
        "change_24h_pct": round(coin_data.get("usd_24h_change", 0), 2),
    }
