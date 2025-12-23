# SimulatedVerse/src/temple/validators.py
from marshmallow import Schema, fields, validates_schema, ValidationError
class KnowledgeSchema(Schema):
    knowledge = fields.Str()
    @validates_schema
    def validate_knowledge(self, data, **kwargs):
        if 'knowledge' not in data:
            raise ValidationError('Missing knowledge field')
# SimulatedVerse/modules/culture_ship/auth.py
import jwt
from flask import request, abort
JWT_SECRET = 'your-256-bit-secret'
def authenticate():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        abort(401)
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        abort(401)
    except jwt.InvalidTokenError:
        abort(401)
    return payload