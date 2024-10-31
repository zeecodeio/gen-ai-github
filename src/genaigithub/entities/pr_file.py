from mongoengine import (
    Document, ReferenceField, StringField, 
    IntField, DateTimeField, EnumField
)
from enum import Enum
from .pull_request import PullRequest

class FileStatus(Enum):
    ADDED = 'added'
    MODIFIED = 'modified'
    REMOVED = 'removed'

class PrFile(Document):
    pull_request = ReferenceField(PullRequest, required=True)
    filename = StringField(required=True)
    status = EnumField(FileStatus)
    additions = IntField(default=0)
    deletions = IntField(default=0)
    changes = IntField(default=0)
    patch = StringField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    meta = {
        'collection': 'pr_files',
        'indexes': [
            {'fields': ['pull_request', 'filename']}
        ]
    } 