# 📈 Crypto Portfolio Tracker

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-yellow)

Real-time crypto portfolio tracker API.  
Prices are fetched from [CoinGecko](https://coingecko.com) — **free, no API key required**.

## ✨ Features

- Real-time prices for 20+ coins
- 24h price change (%)
- Total portfolio value in USD
- Interactive API docs (Swagger UI)
- Async requests — fast and efficient

## 🛠 Stack

- **Python 3.11+**
- **FastAPI** — web framework
- **httpx** — async HTTP requests to CoinGecko
- **Pydantic v2** — data validation

## 🚀 Getting Started

```bash
git clone https://github.com/YOUR_USERNAME/crypto-tracker.git
cd crypto-tracker
pip install -r requirements.txt
uvicorn main:app --reload
```

Open in browser: **http://127.0.0.1:8000/docs**

## 📡 Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/coins` | List supported coins |
| `POST` | `/portfolio/add` | Add coin to portfolio |
| `DELETE` | `/portfolio/remove/{ticker}` | Remove coin |
| `GET` | `/portfolio` | Portfolio with live prices |
| `GET` | `/price/{ticker}` | Price of a single coin |

## 💡 Usage Examples

```bash
# Add 0.5 BTC
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{"ticker": "btc", "amount": 0.5}'

# View portfolio
curl http://localhost:8000/portfolio

# Get single coin price
curl http://localhost:8000/price/eth
```

## 💰 Supported Coins

`BTC` `ETH` `SOL` `BNB` `XRP` `ADA` `DOGE` `TON` `AVAX` `DOT` `MATIC` `LINK` `UNI` `ATOM` `LTC` `NEAR` `APT` `SUI` `OP` `ARB`

## 📄 License

MIT
