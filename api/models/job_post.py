from mongoengine import Document, StringField, ListField, DictField, ReferenceField, CASCADE
from api.models.user import User
from api.models.batch import Batch

class JobPost(Document):
    usedId = ReferenceField(User,required = True, reverse_delete_rule=CASCADE)
    batchId = ReferenceField(Batch,required = True, reverse_delete_rule=CASCADE)
    job_post = StringField(required=True)
    job_post_data= DictField(default={})
    selected_cvs = ListField(DictField(default={}))
    