from pydantic import BaseModel

class VideoRequest(BaseModel):
    url: str

class QueryRequest(BaseModel):
    query: str
    session_id: str

class SessionRequest(BaseModel):
    session_id: str