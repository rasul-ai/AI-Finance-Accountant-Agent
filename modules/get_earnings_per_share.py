# modules/get_earnings_per_share.py
from api.endpoints import FMPEndpoints

class GetEarningsPerShare:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_key_metrics(ticker, year=year)
            if not data:
                return f"Error: No earnings per share data available for {ticker}."
            value = data[0].get("eps", 0)
            return f"{ticker}'s earnings per share for {year or 'the latest year'} is ${value:.2f}."
        except Exception as e:
            return f"Error fetching earnings per share: {e}"