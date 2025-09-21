import pandas as pd

# CSV 파일 로드
try:
    badwords = pd.read_csv("llm_dev1/guard.csv", header=None)[0].dropna().tolist()
except FileNotFoundError:
    print("⚠️ guard.csv 파일이 없습니다. 욕설 필터링은 비활성화됩니다.")
    badwords = []

def contains_profanity(text: str) -> bool:
    return any(bad in text for bad in badwords)


def clean_text(text: str) -> str:
    for bad in badwords:
        text = text.replace(bad, "*" * len(bad))
    return text
