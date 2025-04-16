# modules/get_stock_price.py
from api.endpoints import FMPEndpoints

class GetStockPrice:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_quote_short(ticker)
            if not data:
                return f"Error: No stock price data available for {ticker}."
            value = data[0].get("price", 0)
            return f"{ticker}'s current stock price is ${value:.2f}."
        except Exception as e:
            return f"Error fetching stock price: {e}"