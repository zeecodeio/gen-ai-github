from mongoengine import Document, ReferenceField, StringField, IntField, DateTimeField, EnumField
from enum import Enum
from .repository import Repository


class PRStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class PullRequest(Document):
    repository = ReferenceField(Repository, required=True)
    pr_number = IntField(required=True)
    title = StringField(required=True)
    description = StringField()
    author = StringField(required=True)
    status = EnumField(PRStatus, required=True)
    base_branch = StringField()
    head_branch = StringField()
    created_at = DateTimeField()
    updated_at = DateTimeField()
    closed_at = DateTimeField()

    meta = {"collection": "pull_requests", "indexes": [{"fields": ["repository", "pr_number"], "unique": True}]}
