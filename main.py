# main.py
import asyncio
import importlib
from voice.speech_to_text import SpeechToText
from voice.intent_classifier import IntentClassifier
# from voice.classifier import TextClassifier
from api.endpoints import FMPEndpoints
from rag.retriever import Retriever
from rag.sql_db import SQL_Key_Pair
from rag.web_search import duckduckgo_web_search

async def process_query(vosk_model_path, audio_data=None, query_text=None, use_retriever=False):
    # Step 1: Initialize components
    stt = SpeechToText(model_path=vosk_model_path)
    classifier = IntentClassifier()
    # classifier = TextClassifier()
    endpoints = FMPEndpoints()
    # initialize rag tools
    retriever = Retriever(file_path="./data/financial_data.csv")
    sql_db = SQL_Key_Pair(file_path="./data/financial_data.csv")

    # Output format
    output = {
        "User asked": "",
        "intent": "",
        "entities": "",
        "base_response": "",
        "retriever_response": "",
        "web_search_response": "",
        "final_response": "",
        "error": ""
    }

    try:
        # Step 2: Process input (text or audio)
        if audio_data:
            text = stt.transcribe_audio(audio_data)
            if not text:
                output["error"] = "Could not understand the audio."
                return output
        elif query_text:
            text = query_text
        else:
            output["error"] = "No audio or text query provided."
            return output

        output["User asked"] = text

        # Step 3: Classify intent (zero-shot) and extract entities
        intent = classifier.classify_with_llm(text)
        output["intent"] = intent if intent else "Could not classify intent."

        entities = classifier.extract_entities(text)
        output["entities"] = str(entities)

        if intent:
            intent_to_module = {
                "get_net_income": ("modules.get_net_income", "GetNetIncome"),
                "get_revenue": ("modules.get_revenue", "GetRevenue"),
                "get_stock_price": ("modules.get_stock_price", "GetStockPrice"),
                "get_profit_margin": ("modules.get_profit_margin", "GetProfitMargin"),
                "get_company_profile": ("modules.get_company_profile", "GetCompanyProfile"),
                "get_market_cap": ("modules.get_market_cap", "GetMarketCap"),
                "get_historical_stock_price": ("modules.get_historical_stock_price", "GetHistoricalStockPrice"),
                "get_dividend_info": ("modules.get_dividend_info", "GetDividendInfo"),
                "get_balance_sheet": ("modules.get_balance_sheet", "GetBalanceSheet"),
                "get_cash_flow": ("modules.get_cash_flow", "GetCashFlow"),
                "get_financial_ratios": ("modules.get_financial_ratios", "GetFinancialRatios"),
                "get_earnings_per_share": ("modules.get_earnings_per_share", "GetEarningsPerShare"),
                "get_interest": ("modules.get_interest", "GetInterest"),
                "get_income_tax": ("modules.get_income_tax", "GetIncomeTax"),
                "get_cost_info": ("modules.get_cost_info", "GetCostInfo"),
                "get_research_info": ("modules.get_research_info", "GetResearchInfo")
                
            }

            # Identify module for API calling
            module_info = intent_to_module.get(intent)
            if module_info:
                module_path, class_name = module_info
                try:
                    module = importlib.import_module(module_path)
                    class_instance = getattr(module, class_name)()
                    ticker = entities["ticker"]

                    # Step 4: Get the base response from the module
                    base_response = None
                    try:
                        base_response = await class_instance.get_data(
                            ticker=ticker,
                            year=entities["year"],
                            date=entities["date"],
                        )
                    except Exception as e:
                        base_response = f"Error fetching base response: {e}"
                    

                    # Step 5: Handle the response based on requirements
                    final_response = None
                    if base_response and "Error" not in str(base_response) and "None" not in str(base_response):
                        # Base response succeeded
                        final_response = base_response
                        output["base_response"] = f"{final_response}"
                        
                        # Use retriever if specified (optional)
                        if use_retriever:
                            # retriever_response = retriever.retrieve(text, entities)
                            # retriever_response = sql_db.entity_based_query(entities)
                            retriever_response = sql_db.query_db(entities["ticker"], entities["metric"])
                            final_response = f"{final_response} Additional Info found in the CSV: {retriever_response}"
                            output["retriever_response"] = retriever_response
                    else:
                        # Base response failed, use the retriever
                        output["base_response"] = f"{base_response} Using retriever to query CSV file..."
                        # retriever_response = retriever.retrieve(text, entities)
                        # retriever_response = sql_db.keyword_match_search(entities)
                        retriever_response = sql_db.query_db(entities["ticker"], entities["metric"])
                        output["retriever_response"] = retriever_response

                        if "No relevant data found" in retriever_response:
                            # If both API and rag failed to extract information, search on the web
                            search_results = duckduckgo_web_search(text)
                            if search_results:
                                output["web_search_response"] = search_results[0]['snippet']
                                final_response = search_results[0]['snippet']
                            else:
                                output["web_search_response"] = "No relevant data found on the web."
                                final_response = "No relevant data found on the web."
                        else:
                            final_response = retriever_response

                    output["final_response"] = final_response
                except ImportError as e:
                    output["error"] = f"Module import error: {e}"
                except AttributeError as e:
                    output["error"] = f"Class not found in module: {e}"
                except Exception as e:
                    output["error"] = f"Error processing intent {intent}: {e}"
            else:
                output["error"] = f"Unsupported intent: {intent}"
        else:
            output["error"] = "Could not classify intent."

    except Exception as e:
        output["error"] = f"Unexpected error: {e}"

    # print(output)
    # Return output to the User Interface
    return output
