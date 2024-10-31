from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from genaigithub.config.env_config import mongodb_uri, mongodb_database
from typing import Optional


class MongoDB:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self):
        # Get MongoDB configuration from EnvConfig
        mongodb_uri = mongodb_uri
        database_name = mongodb_database

        try:
            # Create MongoDB client
            self._client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test the connection
            self._client.admin.command("ping")
            print(f"Successfully connected to MongoDB at {mongodb_uri}")
            self._db = self._client[database_name]

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def get_database(self):
        """Get the database instance"""
        return self._db

    def get_collection(self, collection_name: str):
        """Get a specific collection"""
        return self._db[collection_name]

    def close_connection(self):
        """Close the MongoDB connection"""
        if self._client:
            self._client.close()
            print("MongoDB connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()
