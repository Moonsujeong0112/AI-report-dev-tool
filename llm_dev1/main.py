import os
from typing import List
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, FileResponse
from fastapi import Request
from llm_dev1.schemas import ChatRequest, ChatResponse, UsageStats, ChatHistoryItem
from llm_dev1 import llm_provider
from llm_dev1.usage_tracker import usage_tracker
from llm_dev1.rag_engine import build_prompt
from llm_dev1.guardrail import contains_profanity
from llm_dev1.llm_provider import chat as gemini_chat



app = FastAPI(
    title="LLM FastAPI (Gemini)",
    version="0.1.0",
    description="FastAPI backend for Google Gemini API with usage tracking.",
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/history")
def get_chat_history(limit: int = 100):
    return usage_tracker.get_history(limit=limit)

@app.get("/favicon.ico")
def get_favicon():
    """파비콘 요청을 처리합니다."""
    # 간단한 SVG 파비콘을 반환
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="#667eea"/>
        <text x="50" y="65" font-size="50" text-anchor="middle" fill="white">🤖</text>
    </svg>'''
    return Response(content=svg_content, media_type="image/svg+xml")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "provider": os.getenv("PROVIDER", "gemini"),
        "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "env": os.getenv("APP_ENV", "dev"),
        "has_api_key": bool(os.getenv("GEMINI_API_KEY")),
        "api_key_length": len(os.getenv("GEMINI_API_KEY", "")),
        "api_key_preview": os.getenv("GEMINI_API_KEY", "")[-4:] if os.getenv("GEMINI_API_KEY") else "None"
    }

@app.get("/debug/env")
def debug_env():
    """환경 변수 디버깅 정보를 반환합니다."""
    return {
        "PROVIDER": os.getenv("PROVIDER"),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL"),
        "GEMINI_API_KEY": "***" + os.getenv("GEMINI_API_KEY", "")[-4:] if os.getenv("GEMINI_API_KEY") else None,
        "APP_ENV": os.getenv("APP_ENV"),
        "PYTHONPATH": os.getenv("PYTHONPATH"),
        "current_working_dir": os.getcwd(),
        "files_in_current_dir": os.listdir(".") if os.path.exists(".") else []
    }

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # 1. 최신 user 메시지만 추출 (항상 존재한다고 가정)
    latest_msg = req.messages[-1]

    # 2. RAG 미사용이므로 system 메시지는 제거하고 질문만 넘김
    cleaned_messages = [
        m for m in req.messages
        if m.role == "user" or m.role == "assistant"
    ]

    # (선택) 만약 마지막 메시지만 보내고 싶다면 이렇게도 가능:
    # cleaned_messages = [latest_msg]

    # 3. LLM에 전달
    result = llm_provider.chat(
        messages=[{"role": m.role, "content": m.content} for m in cleaned_messages],
        temperature=req.temperature,
        max_tokens=req.max_tokens
    )
    return ChatResponse(**result)

@app.get("/usage/stats", response_model=UsageStats)
def get_usage_stats():
    """사용량 통계를 반환합니다."""
    return usage_tracker.get_stats()

@app.get("/usage/history", response_model=List[ChatHistoryItem])
def get_chat_history(limit: int = 50):
    """채팅 히스토리를 반환합니다."""
    return usage_tracker.get_history(limit=limit)

@app.get("/usage/reset")
def reset_usage_stats():
    """사용량 통계를 리셋합니다. (개발용)"""
    # 실제로는 관리자 권한 확인이 필요
    usage_tracker.stats.total_requests = 0
    usage_tracker.stats.total_tokens_input = 0
    usage_tracker.stats.total_tokens_output = 0
    usage_tracker.stats.total_cost = 0.0
    usage_tracker.stats.requests_today = 0
    usage_tracker.stats.tokens_today = 0
    usage_tracker.stats.cost_today = 0.0
    usage_tracker.stats.last_request_time = None
    usage_tracker._save_stats()
    return {"message": "Usage stats reset successfully"}

@app.post("/rag-test")
def rag_prompt_test(
    metadata: str = Form(...),
    chat_log: str = Form(...),
    rag_criteria: str = Form(...),
    user_input: str = Form(...),
    temperature: float = Form(0.7),
    max_tokens: int = Form(1000),
):
    if contains_profanity(user_input):
        return JSONResponse(status_code=400, content={"error": "입력에 금지어가 포함되어 있습니다."})

    full_prompt = build_prompt(metadata, chat_log, rag_criteria, user_input)

    result = gemini_chat(
        messages=[{"role": "user", "content": full_prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )

    return {
        "prompt": full_prompt,
        "response": result["content"],
        "tokens_input": result["tokens_input"],
        "tokens_output": result["tokens_output"],
        "cost": result["cost"]
    }
    
# ✅ 사용량 통계 반환 API
@app.get("/api/stats")
def get_stats():
    """usage_stats.json 파일 내용 반환"""
    return usage_tracker.get_stats().dict()

# ✅ 대화 히스토리 반환 API
@app.get("/api/history")
def get_history(limit: int = 100):
    """chat_history.json 파일 내용 반환 (최대 N개)"""
    history = usage_tracker.get_history(limit=limit)
    return [item.dict() for item in history]

# 정적 파일 제공 (API 엔드포인트 뒤에 배치)
app.mount("/static", StaticFiles(directory="llm_dev1/static"), name="static")

@app.get("/")
async def read_index():
    """루트 경로에서 index.html을 제공합니다."""
    return FileResponse("llm_dev1/static/index.html")

