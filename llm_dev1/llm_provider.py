import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from .usage_tracker import usage_tracker

PROVIDER = os.getenv("PROVIDER", "gemini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# SDK 초기화
if PROVIDER == "gemini":
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        _model = genai.GenerativeModel(GEMINI_MODEL)
        print(f"✅ Gemini 모델 초기화 완료: {GEMINI_MODEL}")
    except Exception as e:
        print(f"❌ Gemini 모델 초기화 실패: {e}")
        raise

def _to_gemini_contents(messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    contents = []
    for m in messages:
        g_role = "model" if m.get("role") == "assistant" else "user"
        contents.append({"role": g_role, "parts": [m.get("content", "")]})
    return contents

def _count_tokens(text: str) -> int:
    """Gemini 공식 토크나이저 사용"""
    try:
        return _model.count_tokens(text).total_tokens
    except Exception as e:
        print(f"⚠️ 토큰 계산 실패 (fallback 사용): {e}")
        return len(text) // 2

def _extract_text(candidate) -> str:
    try:
        content = getattr(candidate, 'content', None)
        if content and hasattr(content, 'parts') and content.parts:
            return "".join(part.text for part in content.parts if hasattr(part, "text") and part.text)
        elif content and hasattr(content, 'text') and content.text:
            return content.text
    except Exception as e:
        print(f"❌ 텍스트 추출 실패: {e}")
    return ""

def _describe_finish_reason(reason_code: int) -> str:
    return {
        0: "미지정",
        1: "정상 완료",
        2: "MAX_TOKENS (최대 토큰 수 도달)",
        3: "SAFETY (안전성 위반)",
        4: "RECITATION (복사/붙여넣기 감지)",
        5: "기타 오류"
    }.get(reason_code, f"알 수 없음 ({reason_code})")

def chat(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> Dict[str, str]:
    if PROVIDER != "gemini":
        raise RuntimeError("Only 'gemini' provider is supported in this setup.")

    try:
        contents = _to_gemini_contents(messages)
        max_tokens = min(max_tokens or 512, 10000)
        gen_cfg = {
            "temperature": temperature,
            "max_output_tokens": max_tokens
        }

        # 입력 텍스트 토큰 계산
        input_text = " ".join([m.get("content", "") for m in messages])
        tokens_input = _count_tokens(input_text)

        print(f"🔍 Gemini API 요청:")
        print(f"   모델: {GEMINI_MODEL}")
        print(f"   입력 토큰: {tokens_input}")
        print(f"   설정: {gen_cfg}")

        resp = _model.generate_content(contents=contents, generation_config=gen_cfg)

        out_text = ""
        finish_reason = None

        if resp.candidates:
            candidate = resp.candidates[0]
            finish_reason = getattr(candidate, "finish_reason", None)
            print(f"📤 Gemini 응답 분석: finish_reason = {finish_reason} ({_describe_finish_reason(finish_reason)})")

            out_text = _extract_text(candidate).strip()
            tokens_output = _count_tokens(out_text)

            if finish_reason == 2 and tokens_output >= 50:
                out_text += "\n\n⚠️ 응답이 길어 중간에 잘렸을 수 있어요."
            elif finish_reason == 2 and tokens_output < 50:
                print("⚠️ MAX_TOKENS 반환되었지만 응답이 짧아 안내문 생략")
            elif finish_reason == 3:
                out_text = "⚠️ 안전 정책에 의해 응답이 차단됐습니다."
            elif finish_reason == 4:
                out_text = "⚠️ 복사된 콘텐츠가 감지돼 응답이 제한되었습니다."
            elif finish_reason == 5:
                out_text += "\n\n⚠️ Gemini 응답 오류가 감지되었습니다."

        if not out_text:
            out_text = "⚠️ Gemini가 응답을 생성하지 못했습니다. 질문을 다시 시도해 보세요."
            tokens_output = 0

        cost = usage_tracker.estimate_cost(tokens_input, tokens_output)

        usage_tracker.record_chat(
            user_message=messages[-1].get("content", "") if messages else "",
            assistant_message=out_text,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost=cost,
        )

        print(f"✅ 응답 생성 완료: 출력 토큰={tokens_output}, 비용=${cost:.6f}")

        return {
            "content": out_text,
            "model": GEMINI_MODEL,
            "provider": "gemini",
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "cost": cost,
        }

    except Exception as e:
        print(f"❌ Gemini API 호출 실패: {e} ({type(e).__name__})")
        return {
            "content": f"죄송합니다. AI 서비스 오류가 발생했습니다. ({e})",
            "model": GEMINI_MODEL,
            "provider": "gemini",
            "tokens_input": 0,
            "tokens_output": 0,
            "cost": 0.0,
        }
