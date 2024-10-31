from mongoengine import (
    Document, ReferenceField, StringField, 
    IntField, DateTimeField, EnumField, DictField
)
from enum import Enum
from .pull_request import PullRequest
from .pr_file import PrFile

class SuggestionStatus(Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'

class AiSuggestion(Document):
    pull_request = ReferenceField(PullRequest, required=True)
    pr_file = ReferenceField(PrFile, required=True)
    suggestion = StringField(required=True)
    line_number = IntField()
    original_code = StringField()
    suggested_code = StringField()
    status = EnumField(SuggestionStatus, default=SuggestionStatus.PENDING)
    reasoning = StringField()
    metadata = DictField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    meta = {
        'collection': 'ai_suggestions',
        'indexes': [
            {'fields': ['pull_request', 'pr_file']}
        ]
    } 