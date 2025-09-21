# Python 베이스 이미지
FROM python:3.10-slim-bullseye

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# requirements 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스코드 복사
COPY . .

# 포트 노출
EXPOSE 80

# 실행 명령
CMD ["uvicorn", "llm_dev1.main:app", "--host", "0.0.0.0", "--port", "80"]
