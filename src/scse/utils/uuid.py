import uuid

def short_uuid():
    return str(uuid.uuid4())[:8]
