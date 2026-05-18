import uuid
from pathlib import Path


def attachment_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"attachments/{instance.team_id}/{uuid.uuid4()}{suffix}"