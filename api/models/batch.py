from mongoengine import Document, StringField, ListField, DictField, ReferenceField, CASCADE
from api.models.user import User

class Batch(Document):
    userId = ReferenceField(User,required = True, reverse_delete_rule=CASCADE)
    cv_list=ListField(DictField())
    splitted_docs = DictField()
    namespace= StringField()