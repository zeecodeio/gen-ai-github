from enum import Enum
from mongoengine import (
    Document, 
    ReferenceField, 
    StringField, 
    DateTimeField, 
    DictField,
    EnumField
)
from .pull_request import PullRequest
from .pr_file import PrFile
from datetime import datetime

class SuggestionStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    IMPLEMENTED = "IMPLEMENTED"

class AiSuggestion(Document):
    pull_request = ReferenceField(PullRequest, required=True)
    pr_file = ReferenceField(PrFile)  # Optional, can be None for general PR suggestions
    suggestion = StringField(required=True)
    status = EnumField(SuggestionStatus, default=SuggestionStatus.PENDING)
    created_at = DateTimeField(required=True)
    updated_at = DateTimeField()
    metadata = DictField()  # For storing additional data like context, confidence, etc.

    meta = {
        'collection': 'ai_suggestions',
        'indexes': [
            'pull_request',
            'pr_file',
            'status',
            'created_at'
        ]
    }

    def update_status(self, new_status: SuggestionStatus):
        """Update the suggestion status"""
        self.status = new_status
        self.updated_at = datetime.now()
        self.save()