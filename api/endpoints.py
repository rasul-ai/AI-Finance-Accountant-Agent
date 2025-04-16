# api/endpoints.py
import httpx
import os

class FMPEndpoints:
    def __init__(self):
        # self.db = FinancialDB()
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        # print(self.fmp_api_key)
        self.base_url = "https://financialmodelingprep.com/api/v3"

    async def get_income_statement(self, ticker, year=None, period="annual", limit=1):
        """
        Fetch income statement data for a given ticker.
        """
        endpoint = f"{self.base_url}/income-statement/{ticker}"
        params = {"apikey": self.fmp_api_key, "period": period, "limit": limit}
        if year:
            params["year"] = year
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error fetching income statement: {e}")

    async def get_quote_short(self, ticker):
        """
        Fetch the current stock price (short quote) for a given ticker.
        """
        endpoint = f"{self.base_url}/quote-short/{ticker}"
        params = {"apikey": self.fmp_api_key}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error fetching quote: {e}")

    async def get_ratios(self, ticker, year=None, limit=1):
        """
        Fetch financial ratios for a given ticker.
        """
        endpoint = f"{self.base_url}/ratios/{ticker}"
        params = {"apikey": self.fmp_api_key, "limit": limit}
        if year:
            params["year"] = year
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error fetching ratios: {e}")

    async def get_profile(self, ticker):
        """
        Fetch company profile data for a given ticker.
        """
        endpoint = f"{self.base_url}/profile/{ticker}"
        params = {"apikey": self.fmp_api_key}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error fetching profile: {e}")

    async def get_historical_price(self, ticker, date=None):
        """
        Fetch historical stock price for a given ticker on a specific date.
        """
        endpoint = f"{self.base_url}/historical-price-full/{ticker}"
        params = {"apikey": self.fmp_api_key}
        if date:
            params["from"] = date
            params["to"] = date
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error fetching historical price: {e}")

    async def get_balance_sheet(self, ticker, year=None, period="annual", limit=1):
        """
        Fetch balance sheet data for a given ticker.
        """
        endpoint = f"{self.base_url}/balance-sheet-statement/{ticker}"
        params = {"apikey": self.fmp_api_key, "period": period, "limit": limit}
        if year:
            params["year"] = year
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error fetching balance sheet: {e}")

    async def get_cash_flow(self, ticker, year=None, period="annual", limit=1):
        """
        Fetch cash flow statement data for a given ticker.
        """
        endpoint = f"{self.base_url}/cash-flow-statement/{ticker}"
        params = {"apikey": self.fmp_api_key, "period": period, "limit": limit}
        if year:
            params["year"] = year
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error fetching cash flow: {e}")

    async def get_key_metrics(self, ticker, year=None, limit=1):
        """
        Fetch key metrics (e.g., EPS) for a given ticker.
        """
        endpoint = f"{self.base_url}/key-metrics/{ticker}"
        params = {"apikey": self.fmp_api_key, "limit": limit}
        if year:
            params["year"] = year
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error fetching key metrics: {e}")