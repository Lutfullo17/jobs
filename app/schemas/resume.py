from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CandidateResumeOut(BaseModel):
    id: int
    candidate_id: int
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    updated_at: datetime

    download_url: str

    model_config = ConfigDict(from_attributes=True)

