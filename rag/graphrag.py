import os
from neo4j import GraphDatabase
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.neo4jvector import Neo4jVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


class GraphRAGRetriever:
    def __init__(self, neo4j_url, neo4j_username, neo4j_password):
        # Set up the embedding model
        self.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Set up the Ollama LLM
        self.llm = Ollama(model="gemma:2b", request_timeout=None)

        # Configure Settings
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model

        # Set up the Neo4j driver
        self.driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_username, neo4j_password))

        # Set up the Neo4j vector store
        self.vector_store = Neo4jVectorStore(
            url=neo4j_url,
            username=neo4j_username,
            password=neo4j_password,
            embedding_dimension=384,  # Matches MiniLM model
            driver=self.driver
        )

    def ingest_documents(self, directory_path):
        # Load documents from the specified directory
        documents = SimpleDirectoryReader(directory_path).load_data()

        # Create the vector index
        index = VectorStoreIndex.from_documents(
            documents,
            vector_store=self.vector_store,
        )

        # Persist the index to disk
        index.storage_context.persist()

    def query(self, question):
        # Load the index from storage
        storage_context = StorageContext.from_defaults(persist_dir="./storage")
        index = load_index_from_storage(storage_context)

        # Create a query engine and execute the query
        query_engine = index.as_query_engine()
        response = query_engine.query(question)

        return str(response)


if __name__ == "__main__":
    retriever = GraphRAGRetriever(
        neo4j_url="bolt://localhost:7687/",
        neo4j_username="neo4j",
        neo4j_password=os.getenv("NEO4J_PASSWORD")
    )
    retriever.ingest_documents("/home/bapary/Music/AI Finance Agent/rag/data")
    answer = retriever.query("What is the revenue of Company Microsoft in 2021?")
    print(answer)
