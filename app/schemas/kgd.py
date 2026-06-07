from pydantic import BaseModel


class KgdStatusRead(BaseModel):
    mode: str
    api_key_configured: bool
    base_url_configured: bool
