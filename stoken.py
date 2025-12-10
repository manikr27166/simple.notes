from itsdangerous import URLSafeTimedSerializer
from config import secret_key,salt

#endcoding serializer
def endata(data):
    serializer=URLSafeTimedSerializer(secret_key)
    return serializer.dumps(data,salt=salt)

#decoding serializer
def dndata(data):
    serializer=URLSafeTimedSerializer(secret_key)
    return serializer.loads(data,salt=salt)