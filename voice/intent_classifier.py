# voice/intent_classifier.py
import spacy
from transformers import pipeline
from dateutil.parser import parse
import re
import pandas as pd
from difflib import SequenceMatcher

class IntentClassifier:
    def __init__(self):
        # Use a larger model for better NER (optional)
        self.nlp = spacy.load("en_core_web_lg")  # "en_core_web_sm"
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        self.intents = [
            "get_net_income",
            "get_revenue",
            "get_stock_price",
            "get_profit_margin",
            "get_company_profile",
            "get_market_cap",
            "get_historical_stock_price",
            "get_dividend_info",
            "get_balance_sheet",
            "get_cash_flow",
            "get_financial_ratios",
            "get_earnings_per_share",
            "get_interest",
            "get_research_info",
            "get_cost_info",
            "get_income_tax"
        ]

        # Mapping of company names to ticker symbols (case-insensitive)
        self.company_to_ticker = {
            "apple": "AAPL",
            "microsoft corporation": "MSFT",
            "microsoft": "MSFT",
            "nvidia corporation": "NVDA",
            "nvidia": "NVDA",
            "amazon": "AMZN",
            "alphabet inc": "GOOGL",
            "google": "GOOGL",
            "meta platforms": "META",
            "meta": "META",
            "facebook": "META",
            "tesla": "TSLA",
            "walmart inc": "WMT",
            "walmart": "WMT",
            "visa inc": "V",
            "visa": "V",
            "coca cola": "KO"
        }
        
# Mapping of keywords to intents (case-insensitive)
        self.intent_to_keywords = {
            "get_net_income": ["net income", "income", "earnings"],
            "get_revenue": ["revenue", "sales", "turnover", "gross income"],
            "get_stock_price": ["stock price", "stock", "price", "share price", "current price", "price now", "stock value"],
            "get_profit_margin": ["profit margin", "margin", "profit percentage", "net margin", "profit"],
            "get_company_profile": ["who is", "company profile", "about company", "company info"],
            "get_market_cap": ["market cap", "market capitalization", "company value", "valuation"],
            "get_historical_stock_price": ["historical stock price", "stock price on", "past stock price", "stock price in", "price on"],
            "get_dividend_info": ["dividend info", "dividend payout", "payout ratio", "dividend yield", "dividend"],
            "get_balance_sheet": ["balance sheet", "sheet", "financial position", "assets and liabilities", "balance"],
            "get_cash_flow": ["cash", "flow", "cash flow", "cashflow", "cash from operations", "operating cash"],
            "get_financial_ratios": ["financial ratios", "ratios", "current ratio", "liquidity ratio", "debt ratio"],
            "get_earnings_per_share": ["earnings per share", "eps", "per share earnings"],
        }

    def classify_by_keywords(self, text):
        """
        Classify the intent based on keyword mapping.

        Args:
            text (str): The input text to classify.

        Returns:
            str: The predicted intent, or None if no match is found.
        """
        text_lower = text.lower()
        for intent, keywords in self.intent_to_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                print(f"Classified intent: {intent} based on keywords: {keywords}")
                return intent
        print("No intent matched based on keywords.")
        return None  # Fallback if no keywords match


    def classify_with_llm(self, text):
        try:
            hypothesis_template = "This text is requesting {} information."
            result = self.classifier(text, candidate_labels=self.intents, hypothesis_template=hypothesis_template, multi_label=False)
            predicted_intent = result["labels"][0]
            print(f"Predicted intent: {predicted_intent} with scores: {dict(zip(result['labels'], result['scores']))}")
            return predicted_intent
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return None

    def extract_entities(self, text):
        doc = self.nlp(text)
        entities = {"ticker": None, "metric": None, "year": None, "date": None}

        # Step 1: Extract entities using spaCy NER
        for ent in doc.ents:
            if ent.label_ == "ORG":
                org_name = ent.text.lower()
                ticker = self.company_to_ticker.get(org_name)
                if ticker:
                    entities["ticker"] = ticker
                else:
                    # If not found in the mapping, search in the CSV file
                    try:
                        # Load the CSV file (adjust the path as needed)
                        csv_path = "financial data sp500 companies.csv"  # Same path as used in Retriever
                        df = pd.read_csv(csv_path)

                        # Ensure the required columns exist
                        if "firm" not in df.columns or "Ticker" not in df.columns:
                            print("Required columns 'firm' or 'Ticker' not found in CSV. Using fallback ticker.")
                            entities["ticker"] = ent.text.upper()
                        else:
                            # Calculate similarity scores between org_name and each firm name
                            df["similarity"] = df["firm"].apply(
                                lambda x: SequenceMatcher(None, org_name, str(x).lower()).ratio()
                            )

                            # Find rows with similarity >= 80%
                            matches = df[df["similarity"] >= 0.5]

                            if not matches.empty:
                                # Take the first match (highest similarity)
                                best_match = matches.sort_values(by="similarity", ascending=False).iloc[0]
                                ticker = best_match["Ticker"]
                                print(f"Found ticker {ticker} for {org_name} with similarity {best_match['similarity']:.2f}")
                                entities["ticker"] = ticker
                            else:
                                print(f"No match found for {org_name} with >= 50% similarity. Using fallback ticker.")
                                entities["ticker"] = ent.text.upper()

                    except Exception as e:
                        print(f"Error searching CSV for ticker: {e}. Using fallback ticker.")
                        entities["ticker"] = ent.text.upper()
            elif ent.label_ == "DATE":
                date_text = ent.text.lower()
                try:
                    parsed_date = parse(date_text, fuzzy=True, default=parse("2025-01-01"))
                    # If the date is a year (e.g., "2023", "this year") or parsed as January 1
                    if "year" in date_text or date_text.isdigit() or (parsed_date.day == 1 and parsed_date.month == 1):
                        entities["year"] = parsed_date.strftime("%Y")
                    else:
                        # Otherwise, treat it as a specific date (e.g., "Jan 5")
                        entities["date"] = parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    # Fallback if parsing fails
                    if "year" in date_text or date_text.isdigit():
                        entities["year"] = date_text
                    else:
                        entities["date"] = date_text

        # Step 2: Fallback ticker extraction if spaCy fails to identify ORG
        if not entities["ticker"]:
            text_lower = text.lower()
            for company_name, ticker in self.company_to_ticker.items():
                if company_name in text_lower:
                    entities["ticker"] = ticker
                    break

        # Step 3: Extract metric using keyword matching with synonyms
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in ["net income", "net", "income"]):
            entities["metric"] = "netIncome"
        elif "revenue" in text_lower:
            entities["metric"] = "revenue"
        elif any(keyword in text_lower for keyword in ["profit margin", "profit", "margin"]):
            entities["metric"] = "netProfitMargin"
        elif any(keyword in text_lower for keyword in ["market cap", "market capitalization", "market"]):
            entities["metric"] = "mktCap"
        elif any(keyword in text_lower for keyword in ["payout ratio", "dividend payout"]):
            entities["metric"] = "payoutRatio"
        elif any(keyword in text_lower for keyword in ["current ratio", "liquidity ratio"]):
            entities["metric"] = "currentRatio"
        elif any(keyword in text_lower for keyword in ["eps", "earnings per share", "earnings"]):
            entities["metric"] = "eps"
        elif any(keyword in text_lower for keyword in ["stock", "stock price", "current price", "valuation", "price"]):
            entities["metric"] = "price"
        elif any(keyword in text_lower for keyword in ["company info", "about company", "who is"]):
            entities["metric"] = "ceo"
        elif any(keyword in text_lower for keyword in ["balance sheet", "sheet", "assets"]):
            entities["metric"] = "Assets&Liabilities"
        elif any(keyword in text_lower for keyword in ["historical", "earnings per share", "earnings"]):
            entities["metric"] = "historical"
        elif any(keyword in text_lower for keyword in ["cash", "flow", "cash flow"]):
            entities["metric"] = "cashFlowFromOperatingActivities"
        elif any(keyword in text_lower for keyword in ["tax"]):
            entities["metric"] = "IncomeTax"
        elif any(keyword in text_lower for keyword in ["interest", "interest expense", "expense"]):
            entities["metric"] = "InterestExpense"
        elif any(keyword in text_lower for keyword in ["research", "research development", "development"]):
            entities["metric"] = "Research"
        elif any(keyword in text_lower for keyword in ["cost", "total cost"]):
            entities["metric"] = "TotalCost"
            
            
        # Step 4: Normalize year (handle "this year", "last year", etc.)
        if entities["year"]:
            year_text = entities["year"].lower()
            current_year = 2025  # Based on the current date (April 04, 2025)
            if "this year" in year_text:
                entities["year"] = str(current_year)
            elif "last year" in year_text:
                entities["year"] = str(current_year - 1)
            elif re.match(r"^\d{4}$", year_text):
                entities["year"] = year_text
            else:
                # If year is not a valid format, unset it
                entities["year"] = None

        return entities