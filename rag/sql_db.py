import os
import pandas as pd
import faiss
import numpy as np
import sqlite3
from .embedder import Embedder
from datetime import datetime

class SQL_Key_Pair:
    def __init__(self, file_path="financial_data.csv", model_name="all-MiniLM-L6-v2", db_path="/app/db/financial_data.db"):
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.embedder = Embedder(model_name)
        self.index = None
        self.documents = []
        self.data = None
        self.embeddings = None
        try:
            self.db_conn = sqlite3.connect(db_path)
            print(f"Connected to SQLite database at {db_path}")
        except sqlite3.OperationalError as e:
            print(f"Failed to connect to database: {e}")
            raise
        self.create_db_table()
        self.load_data(file_path)

    def create_db_table(self):
        """
        Create the custom_financials table in the database if it doesn’t exist.
        """
        cursor = self.db_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_financials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT,
                firm TEXT,
                ticker TEXT,
                date TEXT,
                metric TEXT,
                value REAL,
                last_updated TEXT
            )
        """)
        self.db_conn.commit()
        print("Created custom_financials table")

    def load_data(self, file_path):
        """
        Load financial data from a CSV or Excel file and store it in the database.
        """
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Use .csv or .xlsx.")

            self.data = df
            self.documents = self.data["Ticker"].astype(str).tolist()
            
            cursor = self.db_conn.cursor()
            for _, row in self.data.iterrows():
                firm = row.get("firm", "")
                ticker = row.get("Ticker", "")
                date = row.get("date", "")
                for column in self.data.columns:
                    if pd.notna(row[column]):
                        try:
                            value = float(row[column])
                        except (ValueError, TypeError):
                            value = 0.0
                        cursor.execute("""
                            INSERT INTO custom_financials (source_file, firm, ticker, date, metric, value, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (os.path.basename(file_path), firm, ticker, str(date), column, value, datetime.now().isoformat()))
            self.db_conn.commit()
            print(f"Loaded {len(self.data)} rows from {file_path} into custom_financials.")
            self.build_index()  # Rebuild FAISS index after loading
        except Exception as e:
            print(f"Error loading data: {e}")
            self.documents = []
            self.data = pd.DataFrame()

    def build_index(self):
        """
        Build a FAISS index from the embedded descriptions.
        """
        if not self.documents:
            return
        self.embeddings = self.embedder.embed(self.documents)
        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(self.embeddings)

    def keyword_match_search(self, entities):
        """
        Perform strict keyword match based search from CSV.
        """
        if self.data is None or self.data.empty:
            return "No data loaded."

        ticker = entities.get("ticker", "")
        metric = entities.get("metric", "")
        
        if not ticker or not metric:
            return "No relevant data found."
        
        ticker = ticker.lower()
        metric = metric.lower()

        retrieved_text = ""
        for _, row in self.data.iterrows():
            if str(row.get("Ticker", "")).lower() == ticker:
                for col in self.data.columns:
                    if col.lower() == metric:
                        if pd.isna(row[col]) or row[col] == "":
                            continue
                        value_in_billions = row[col] / 1_000_000_000
                        retrieved_text = f"Retrieved {metric} for {ticker} is : ${value_in_billions:.2f} billion."
                        break
                break

        if not retrieved_text:
            return "No relevant data found."

        return retrieved_text

    def query_csv(self, query, k=3):
        """
        Query the CSV data with a user query.
        """
        retrieved_data = self.retrieve(query, k=k)
        if not retrieved_data:
            return "No relevant data found."

        responses = []
        for entry in retrieved_data:
            try:
                value = float(entry["value"])
                value_in_billions = value / 1_000_000_000
                response = f"{entry['ticker']}'s {entry['metric']} for {entry['year']} was ${value_in_billions:.2f} billion."
            except:
                response = f"{entry['ticker']}'s {entry['metric']} for {entry['year']} was {entry['value']}."
            responses.append(response)

        return "\n".join(responses)

    def entity_based_query(self, entities):
        return self.keyword_match_search(entities)

    def query_db(self, ticker, metric):
        """
        Query the custom_financials table based on ticker and metric, ignoring date and year.
        """
        try:
            cursor = self.db_conn.cursor()
            query = """
                SELECT value FROM custom_financials
                WHERE ticker = ? AND metric = ?
                LIMIT 1
            """
            params = [ticker, metric]
            cursor.execute(query, params)
            result = cursor.fetchone()
            if result:
                value = result[0]
                value_in_billions = value / 1_000_000_000
                return f"{metric} for {ticker}: ${value_in_billions:.2f} billion."
            return f"No relevant data found for {ticker}."
        except Exception as e:
            print(f"Error querying database: {e}")
            return f"Error querying database: {str(e)}"

    def __del__(self):
        try:
            if hasattr(self, 'db_conn') and self.db_conn:
                self.db_conn.close()
                print("Closed SQLite database connection")
        except Exception as e:
            print(f"Error closing database connection: {e}")