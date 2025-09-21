# project/
# │
# ├── llm_dev1/
# │   ├── main.py              # FastAPI 엔트리포인트
# │   ├── llm_provider.py      # Gemini LLM 호출 및 토큰 계산
# │   ├── usage_tracker.py     # 토큰/비용 추적 및 저장
# │   ├── schemas.py           # Pydantic 데이터 모델
# │   ├── static/
# │   │   └── index.html       # 실시간 UI
# │   ├── guardrail.py         # ✅ 욕설/비속어 필터링 로직 추가 필요
# │   ├── rag_engine.py        # ✅ 오답 판별 RAG 데이터 처리 및 삽입
# │   └── db.py                # ✅ PostgreSQL 저장 기능 및 ORM
# │
# ├── data/
# │   ├── usage_stats.json
# │   └── chat_history.json
# │
# ├── .env                     # 환경 변수 (Gemini API Key 등)
# ├── requirements.txt

# uvicorn llm_dev1.main:app --reload --port 8004
# 👉 http://localhost:8004
#  → 실시간 RAG 테스트 UI

# 👉 http://localhost:8004/api/stats
#  → 사용량 JSON

# 👉 http://localhost:8004/api/history
#  → 채팅 히스토리 JSON