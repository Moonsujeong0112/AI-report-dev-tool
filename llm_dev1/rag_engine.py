def build_prompt(metadata: str, chat_log: str, rag_criteria: str, user_input: str) -> str:
    return f"""
[문제 정보]
{metadata}

[채팅 기록]
{chat_log}

[오답 판별 기준]
{rag_criteria}

[사용자 입력]
{user_input}

"""


# """
# [문제 정보]
# {metadata}

# [채팅 기록]
# {chat_log}

# [오답 판별 기준]
# {rag_criteria}

# [사용자 입력]
# {user_input}

# → 위 정보를 종합하여 학습자의 오류를 분석하고 개선 전략을 제시하라.
# """