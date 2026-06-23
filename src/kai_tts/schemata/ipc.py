from pydantic import BaseModel, Field

class DataReceive(BaseModel):
    """Schema for incoming data validation."""
    timestamp: float = Field(..., description="Creation time of the payload")
    text_token: str = Field(..., description="LLM text token to process")

class DataSend(BaseModel):
    """Schema for outgoing data validation."""
    timestamp: float = Field(..., description="Creation time of the payload")
    audio_buffer: bytes = Field(..., description="Synthesized audio data")