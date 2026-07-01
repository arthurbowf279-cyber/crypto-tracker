# 📈 Crypto Portfolio Tracker

Простой REST API для отслеживания крипто-портфолио в реальном времени.  
Цены берутся с [CoinGecko](https://coingecko.com) — бесплатно, без API-ключа.

## Стек

- **Python 3.11+**
- **FastAPI** — веб-фреймворк
- **httpx** — async HTTP-запросы к CoinGecko
- **Pydantic v2** — валидация данных

## Установка и запуск

```bash
# 1. Клонируй репозиторий
git clone https://github.com/YOUR_USERNAME/crypto-tracker.git
cd crypto-tracker

# 2. Установи зависимости
pip install -r requirements.txt

# 3. Запусти сервер
uvicorn main:app --reload
```

Открой в браузере: **http://127.0.0.1:8000/docs**

## Эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| `GET` | `/coins` | Список поддерживаемых монет |
| `POST` | `/portfolio/add` | Добавить монету в портфолио |
| `DELETE` | `/portfolio/remove/{ticker}` | Удалить монету |
| `GET` | `/portfolio` | Портфолио с актуальными ценами |
| `GET` | `/price/{ticker}` | Цена одной монеты |

## Примеры использования

### Добавить BTC в портфолио
```bash
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{"ticker": "btc", "amount": 0.5}'
```

### Добавить ETH
```bash
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{"ticker": "eth", "amount": 2.0}'
```

### Посмотреть портфолио
```bash
curl http://localhost:8000/portfolio
```

Пример ответа:
```json
{
  "assets": [
    {
      "ticker": "BTC",
      "amount": 0.5,
      "price_usd": 67000.0,
      "value_usd": 33500.0,
      "change_24h_pct": 1.25
    },
    {
      "ticker": "ETH",
      "amount": 2.0,
      "price_usd": 3500.0,
      "value_usd": 7000.0,
      "change_24h_pct": -0.8
    }
  ],
  "total_value_usd": 40500.0
}
```

## Поддерживаемые монеты

`BTC` `ETH` `SOL` `BNB` `XRP` `ADA` `DOGE` `TON` `AVAX` `DOT`

## Как запушить на GitHub

```bash
git init
git add .
git commit -m "Initial commit: crypto portfolio tracker"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/crypto-tracker.git
git push -u origin main
```
