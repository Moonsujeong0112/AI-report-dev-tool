from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    content: str
    model: str
    provider: str
    tokens_input: int
    tokens_output: int
    cost: float

class UsageStats(BaseModel):
    total_requests: int
    total_tokens_input: int
    total_tokens_output: int
    total_cost: float
    requests_today: int
    tokens_today: int
    cost_today: float
    last_request_time: Optional[datetime] = None

class ChatHistoryItem(BaseModel):
    timestamp: datetime
    user_message: str
    assistant_message: str
    tokens_used: int
    cost: float

