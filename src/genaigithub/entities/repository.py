from mongoengine import Document, StringField, BooleanField, DateTimeField


class Repository(Document):
    name = StringField(required=True)
    owner = StringField(required=True)
    description = StringField()
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    meta = {"collection": "repositories", "indexes": [{"fields": ["owner", "name"], "unique": True}]}
