# modules/get_market_cap.py
from api.endpoints import FMPEndpoints

class GetMarketCap:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_profile(ticker)
            if not data:
                return f"Error: No market cap data available for {ticker}."
            value = data[0].get("mktCap", 0) / 1_000_000_000
            return f"{ticker}'s market cap is ${value:.2f} billion."
        except Exception as e:
            return f"Error fetching market cap: {e}"