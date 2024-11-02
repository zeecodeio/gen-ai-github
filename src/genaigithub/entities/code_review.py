# src/genaigithub/entities/code_review.py
from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, ListField, StringField, DateTimeField, IntField

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
    created_at = DateTimeField()
    merged_at = DateTimeField()
    changes = ListField(EmbeddedDocumentField(CodeChange))
    reviews = ListField(EmbeddedDocumentField(Review))
    processed_chunks = ListField(DictField())  # Store processed chunks
    last_processed = DateTimeField()  # Track when chunks were last processed
    
    meta = {
        'collection': 'code_reviews',
        'indexes': [
            {'fields': ['repository', 'pr_number'], 'unique': True},
            'created_at',
            'merged_at',
            'last_processed'
        ]
    }