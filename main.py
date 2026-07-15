"""
Crypto Portfolio Tracker
========================
FastAPI service for tracking a crypto portfolio in real time.
Prices are fetched from the CoinGecko API (free, no API key required).

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload

Docs: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx
from typing import Optional

app = FastAPI(
    title="Crypto Portfolio Tracker",
    description="Track your crypto portfolio with real-time prices",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CoinGecko API — free price source, no registration required
# Rate limit: ~30 requests/min on the free tier
# ---------------------------------------------------------------------------
COINGECKO_URL = "https://api.coingecko.com/api/v3"

# Maps ticker symbol to CoinGecko coin ID
# Full list: https://api.coingecko.com/api/v3/coins/list
TICKER_TO_ID: dict[str, str] = {
    "btc":   "bitcoin",
    "eth":   "ethereum",
    "sol":   "solana",
    "bnb":   "binancecoin",
    "xrp":   "ripple",
    "ada":   "cardano",
    "doge":  "dogecoin",
    "ton":   "the-open-network",
    "avax":  "avalanche-2",
    "dot":   "polkadot",
    "matic": "matic-network",
    "link":  "chainlink",
    "uni":   "uniswap",
    "atom":  "cosmos",
    "ltc":   "litecoin",
    "near":  "near",
    "apt":   "aptos",
    "sui":   "sui",
    "op":    "optimism",
    "arb":   "arbitrum",
}

# ---------------------------------------------------------------------------
# In-memory storage (use PostgreSQL in production)
# Structure: { "btc": 0.5, "eth": 2.0, ... }
# ---------------------------------------------------------------------------
portfolio: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AddAssetRequest(BaseModel):
    """Request body for adding a coin to the portfolio."""
    ticker: str = Field(..., example="btc", description="Coin ticker (btc, eth, sol...)")
    amount: float = Field(..., gt=0, example=0.5, description="Amount of coins")


class AssetInfo(BaseModel):
    """Info about a single coin in the portfolio."""
    ticker: str
    amount: float
    price_usd: float
    value_usd: float
    change_24h_pct: Optional[float]  # 24h price change in %


class PortfolioResponse(BaseModel):
    """Full portfolio report."""
    assets: list[AssetInfo]
    total_value_usd: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def fetch_prices(coin_ids: list[str]) -> dict:
    """
    Fetches live prices from CoinGecko.
    Returns: { "bitcoin": {"usd": 65000, "usd_24h_change": 2.5}, ... }
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
            detail="Failed to fetch prices from CoinGecko. Please try again later."
        )

    return response.json()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/coins", summary="List supported coins")
async def list_coins() -> dict:
    """Returns all coins supported by the tracker."""
    return {
        "supported_coins": [
            {"ticker": ticker, "name": coin_id}
            for ticker, coin_id in TICKER_TO_ID.items()
        ]
    }


@app.post("/portfolio/add", summary="Add a coin to the portfolio")
async def add_asset(request: AddAssetRequest) -> dict:
    """
    Adds a coin to the portfolio or increases an existing position.
    Example: { "ticker": "btc", "amount": 0.5 }
    """
    ticker = request.ticker.lower()

    if ticker not in TICKER_TO_ID:
        raise HTTPException(
            status_code=400,
            detail=f"Coin '{ticker}' is not supported. Available: {list(TICKER_TO_ID.keys())}"
        )

    portfolio[ticker] = portfolio.get(ticker, 0) + request.amount

    return {
        "status": "ok",
        "ticker": ticker,
        "total_amount": portfolio[ticker],
        "message": f"Added {request.amount} {ticker.upper()}. Total: {portfolio[ticker]}"
    }


@app.delete("/portfolio/remove/{ticker}", summary="Remove a coin from the portfolio")
async def remove_asset(ticker: str) -> dict:
    """Completely removes a coin from the portfolio."""
    ticker = ticker.lower()

    if ticker not in portfolio:
        raise HTTPException(status_code=404, detail=f"{ticker} not found in portfolio")

    del portfolio[ticker]
    return {"status": "ok", "message": f"{ticker.upper()} removed from portfolio"}


@app.get("/portfolio", summary="Get portfolio with live prices")
async def get_portfolio() -> PortfolioResponse:
    """
    Returns the full portfolio with live prices and total value.
    Prices are fetched from CoinGecko in real time.
    """
    if not portfolio:
        return PortfolioResponse(assets=[], total_value_usd=0)

    coin_ids = [TICKER_TO_ID[ticker] for ticker in portfolio]
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

    assets.sort(key=lambda x: x.value_usd, reverse=True)

    return PortfolioResponse(
        assets=assets,
        total_value_usd=round(total_value, 2),
    )


@app.get("/price/{ticker}", summary="Get price of a single coin")
async def get_price(ticker: str) -> dict:
    """Quick price check for a single coin."""
    ticker = ticker.lower()

    if ticker not in TICKER_TO_ID:
        raise HTTPException(
            status_code=400,
            detail=f"Coin '{ticker}' is not supported"
        )

    coin_id = TICKER_TO_ID[ticker]
    prices_data = await fetch_prices([coin_id])
    coin_data = prices_data.get(coin_id, {})

    return {
        "ticker": ticker.upper(),
        "price_usd": coin_data.get("usd"),
        "change_24h_pct": round(coin_data.get("usd_24h_change", 0), 2),
    }
