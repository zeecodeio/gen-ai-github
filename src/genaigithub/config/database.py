from mongoengine import connect
from genaigithub.config.env_config import (
    mongodb_host,
    mongodb_port,
    mongodb_database,
    mongodb_username,
    mongodb_password,
)


def init_db():
    connect(
        db=mongodb_database,
        host=f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_host}:{mongodb_port}/{mongodb_database}",
        authentication_source="admin",
        serverSelectionTimeoutMS=5000,  # Timeout set to 5 seconds
    )
