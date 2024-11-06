from mongoengine import Document, StringField,BooleanField,DateTimeField
from datetime import datetime

class User(Document):
    first_name = StringField(required=True)
    last_name = StringField()
    email = StringField(required=True, unique=True)
    user_full_name = StringField()
    confirmed = BooleanField(required=True, default=False)
    created_at = DateTimeField(default=datetime.now)
