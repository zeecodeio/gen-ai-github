from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, ListField, StringField, DateTimeField, IntField, ReferenceField, DictField
from .pull_request import PullRequest
from .pr_file import PrFile

class CodeChange(EmbeddedDocument):
    filename = StringField(required=True)
    language = StringField(required=True)
    patch = StringField()
    additions = IntField()
    deletions = IntField()

class Review(EmbeddedDocument):
    reviewer = StringField(required=True)
    comment = StringField()
    state = StringField()
    submitted_at = DateTimeField()

class CodeReview(Document):
    pr_number = IntField(required=True)
    repository = StringField(required=True)
    pull_request = ReferenceField(PullRequest, required=True)  # Add this reference
    pr_files = ListField(ReferenceField(PrFile))  # Add this reference
    created_at = DateTimeField()
    merged_at = DateTimeField()
    changes = ListField(EmbeddedDocumentField(CodeChange))
    reviews = ListField(EmbeddedDocumentField(Review))
    processed_chunks = ListField(DictField())
    last_processed = DateTimeField()
    
    meta = {
        'collection': 'code_reviews',
        'indexes': [
            {'fields': ['repository', 'pr_number'], 'unique': True},
            'created_at',
            'merged_at',
            'last_processed'
        ]
    }