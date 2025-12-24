from pydantic import BaseModel


class UploadRequest(BaseModel):
    filename: str
    content_type: str | None = None

