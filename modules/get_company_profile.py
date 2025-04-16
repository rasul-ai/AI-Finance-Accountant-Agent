# modules/get_company_profile.py
from api.endpoints import FMPEndpoints

class GetCompanyProfile:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_profile(ticker)
            if not data:
                return f"Error: No company profile data available for {ticker}."
            ceo = data[0].get("ceo", "N/A")
            sector = data[0].get("sector", "N/A")
            return f"{ticker}'s CEO is {ceo} and it operates in the {sector} sector."
        except Exception as e:
            return f"Error fetching company profile: {e}"