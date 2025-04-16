# modules/get_historical_stock_price.py
from api.endpoints import FMPEndpoints

class GetHistoricalStockPrice:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_historical_price(ticker, date=date)
            if not data.get("historical"):
                return f"Error: No historical stock price data available for {ticker} on {date}."
            value = data["historical"][0].get("close", 0)
            return f"{ticker}'s stock price on {date} was ${value:.2f}."
        except Exception as e:
            return f"Error fetching historical stock price: {e}"