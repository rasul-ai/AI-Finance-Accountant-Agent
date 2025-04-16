import pandas as pd
import faiss
import numpy as np
from .embedder import Embedder
from fuzzywuzzy import fuzz
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

class Retriever:
    def __init__(self, file_path):
        self.embedder = Embedder(model_name="all-MiniLM-L6-v2")
        self.index = None
        self.documents = []
        self.data = None
        self.embeddings = None
        self.load_file(file_path)
        self.build_index()

    def load_file(self, file_path):
        try:
            if file_path.endswith('.csv'):
                self.data = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                self.data = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Use .csv, .xlsx, or .xls")
            self.documents = self.data["Ticker"].astype(str).tolist()
        except Exception as e:
            print(f"Error loading file: {e}")
            self.documents = []
            self.data = pd.DataFrame()

    def build_index(self):
        if not self.documents:
            return
        self.embeddings = self.embedder.embed(self.documents)
        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(self.embeddings)

    def retrieve(self, query, entities, k=3, threshold=0.7):
        
        query_prompt = f"{entities['ticker']} {entities['metric']} {entities['year']}"
        # print(query_prompt)
        if not self.index or not self.documents or self.data.empty:
            return []

        query_parts = query_prompt.split()
        if len(query_parts) != 3:
            print("Query must follow 'ticker metric year' pattern")
            return []

        query_ticker, query_metric, query_year = query_parts

        # Ticker similarity
        query_ticker_embedding = self.embedder.embed([query_ticker])
        distances, indices = self.index.search(query_ticker_embedding, k)
        ticker_matches = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                ticker = self.data.iloc[idx]["Ticker"]
                similarity_score = 1 - distances[0][i] / 2
                ticker_matches.append((ticker, similarity_score, idx))

        # Metric similarity
        metric_embeddings = self.embedder.embed(self.data.columns.tolist())
        query_metric_embedding = self.embedder.embed([query_metric])[0]
        metric_scores = []
        for col, col_embedding in zip(self.data.columns, metric_embeddings):
            if col.lower() in ["ticker", "year"]:
                continue
            cos_sim = np.dot(query_metric_embedding, col_embedding) / (
                np.linalg.norm(query_metric_embedding) * np.linalg.norm(col_embedding)
            )
            metric_scores.append((col, cos_sim))

        # Year similarity
        if "Year" not in self.data.columns:
            print("No 'Year' column found in data")
            return []
        year_scores = []
        for year in self.data["Year"].astype(str).unique():
            similarity = fuzz.ratio(query_year, year) / 100.0
            year_scores.append((year, similarity))

        # Combine matches
        retrieved_data = []
        seen = set()
        for ticker, ticker_score, idx in ticker_matches:
            if ticker_score < threshold:
                continue
            for metric, metric_score in metric_scores:
                if metric_score < threshold:
                    continue
                for year, year_score in year_scores:
                    if year_score < 0.5:
                        continue
                    combined_score = (ticker_score + metric_score + year_score) / 3
                    match = self.data[
                        (self.data["Ticker"].str.lower() == ticker.lower()) &
                        (self.data["Year"].astype(str) == year) &
                        (self.data[metric].notnull())
                    ]
                    if not match.empty:
                        value = match[metric].iloc[0]
                        key = (ticker, metric, year)
                        if key not in seen:
                            seen.add(key)
                            retrieved_data.append({
                                "ticker": ticker,
                                "metric": metric,
                                "value": value,
                                "year": year,
                                "combined_score": combined_score
                            })

        if retrieved_data:
            # print(retrieved_data)
            retrieved_data.sort(key=lambda x: x["combined_score"], reverse=True)
            best_match = retrieved_data[0]
            answer = answer_question(query, best_match)
            return answer

        return "No relevant data found."

def answer_question(question, retrieved_data):
    """
    Use a lightweight LLM to generate a natural-language answer on CPU.
    
    Args:
        question (str): The question to answer
        retrieved_data (list): List of dictionaries with ticker, metric, value, year
    
    Returns:
        str: Natural-language answer
    """
    # print(question)
    # print(retrieved_data)
    try:
        # Initialize lightweight LLM (llama3.2:3b, CPU-friendly)
        llm = Ollama(model="gemma:2b", num_gpu=0)  # Explicitly disable GPU

        # Minimal prompt for CPU efficiency
        prompt_template = PromptTemplate(
            input_variables=["question", "ticker", "metric", "value", "year"],
            template=(
                "Question: {question}\n"
                "Data: Ticker={ticker}, Metric={metric}, Value={value}, Year={year}\n"
                "Answer concisely, formatting the value with commas."
            )
        )
        # print(prompt_template)

        # Format data
        if not retrieved_data:
            return "No relevant data found."
        
        prompt = prompt_template.format(
            question=question,
            ticker=retrieved_data['ticker'],
            metric=retrieved_data['metric'],
            value=retrieved_data, # formatted_value,
            year=retrieved_data['year']
        )

        # Generate response
        response = llm.invoke(prompt)
        return response.strip()

    except Exception as e:
        print(f"Error generating answer: {e}")
        return "Unable to generate answer."

# def main(file_path, query, question):
#     """
#     Main function to process a query, retrieve results, and answer a question.
    
#     Args:
#         file_path (str): Path to the CSV or Excel file
#         query (str): Query string in 'ticker metric year' format
#         question (str): Natural-language question to answer
    
#     Returns:
#         tuple: (retrieved data, answer)
#     """
#     try:
#         retriever = Retriever(file_path)
#         results = retriever.retrieve(query)
#         answer = answer_question(question, results)
#         return results, answer
#     except Exception as e:
#         print(f"Error processing query: {e}")
#         return [], "Unable to process query."

# if __name__ == "__main__":
#     file_path = "./financial_data.csv"
#     query = "AAPL InterestExpense 2024"
#     question = "What is the InterestExpense of AAPL 2024?"
#     results, answer = main(file_path, query, question)
#     for result in results:
#         print(f"Ticker: {result['ticker']}, Metric: {result['metric']}, Value: {result['value']}, Year: {result['year']}")
#     print(f"Answer: {answer}")