from pydantic import BaseModel, Field

class VisualAsset(BaseModel):
    name: str
    template_path: str
    threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    offset_x: int = 0
    offset_y: int = 0