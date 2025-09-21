import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
from pathlib import Path
from .schemas import UsageStats, ChatHistoryItem

class UsageTracker:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.stats_file = self.data_dir / "usage_stats.json"
        self.history_file = self.data_dir / "chat_history.json"
        
        # 초기 통계 로드 또는 생성
        self.stats = self._load_stats()
        self.history = self._load_history()
    
    def _load_stats(self) -> UsageStats:
        """사용량 통계를 로드합니다."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # datetime 문자열을 datetime 객체로 변환
                    if data.get('last_request_time'):
                        data['last_request_time'] = datetime.fromisoformat(data['last_request_time'])
                    return UsageStats(**data)
            except Exception:
                pass
        
        # 기본 통계 반환
        return UsageStats(
            total_requests=0,
            total_tokens_input=0,
            total_tokens_output=0,
            total_cost=0.0,
            requests_today=0,
            tokens_today=0,
            cost_today=0.0,
            last_request_time=None
        )
    
    def _load_history(self) -> List[ChatHistoryItem]:
        """채팅 히스토리를 로드합니다."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [ChatHistoryItem(**item) for item in data]
            except Exception:
                pass
        return []
    
    def _save_stats(self):
        """사용량 통계를 저장합니다."""
        data = self.stats.dict()
        # datetime 객체를 문자열로 변환
        if data.get('last_request_time'):
            data['last_request_time'] = data['last_request_time'].isoformat()
        
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_history(self):
        """채팅 히스토리를 저장합니다."""
        data = [item.dict() for item in self.history]
        # datetime 객체를 문자열로 변환
        for item in data:
            item['timestamp'] = item['timestamp'].isoformat()
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _reset_daily_stats(self):
        """일일 통계를 리셋합니다."""
        today = date.today()
        if not self.stats.last_request_time or self.stats.last_request_time.date() < today:
            self.stats.requests_today = 0
            self.stats.tokens_today = 0
            self.stats.cost_today = 0.0
    
    def record_chat(self, user_message: str, assistant_message: str, 
                    tokens_input: int, tokens_output: int, cost: float):
        """채팅 사용량을 기록합니다."""
        self._reset_daily_stats()
        
        # 비정상적인 사용량 감지
        if self._detect_abnormal_usage(tokens_input, tokens_output, cost):
            print(f"⚠️  비정상적인 사용량 감지!")
            print(f"   입력 토큰: {tokens_input}")
            print(f"   출력 토큰: {tokens_output}")
            print(f"   비용: ${cost}")
            print(f"   사용자 메시지: {user_message[:100]}...")
        
        # 통계 업데이트
        self.stats.total_requests += 1
        self.stats.total_tokens_input += tokens_input
        self.stats.total_tokens_output += tokens_output
        self.stats.total_cost += cost
        
        self.stats.requests_today += 1
        self.stats.tokens_today += tokens_input + tokens_output
        self.stats.cost_today += cost
        self.stats.last_request_time = datetime.now()
        
        # 히스토리에 추가
        history_item = ChatHistoryItem(
            timestamp=datetime.now(),
            user_message=user_message,
            assistant_message=assistant_message,
            tokens_used=tokens_input + tokens_output,
            cost=cost
        )
        self.history.append(history_item)
        
        # 최근 100개만 유지
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        # 저장
        self._save_stats()
        self._save_history()
    
    def _detect_abnormal_usage(self, tokens_input: int, tokens_output: int, cost: float) -> bool:
        """비정상적인 사용량을 감지합니다."""
        # 입력 토큰이 너무 많은 경우 (예: 10,000 토큰 이상)
        if tokens_input > 10000:
            return True
        
        # 출력 토큰이 너무 많은 경우 (예: 20,000 토큰 이상)
        if tokens_output > 20000:
            return True
        
        # 비용이 너무 높은 경우 (예: $1.00 이상)
        if cost > 1.0:
            return True
        
        # 1분 내에 10번 이상 요청하는 경우
        recent_requests = [item for item in self.history 
                          if (datetime.now() - item.timestamp).seconds < 60]
        if len(recent_requests) > 10:
            return True
        
        return False
    
    def get_stats(self) -> UsageStats:
        """현재 사용량 통계를 반환합니다."""
        self._reset_daily_stats()
        return self.stats
    
    def get_history(self, limit: int = 50) -> List[ChatHistoryItem]:
        """최근 채팅 히스토리를 반환합니다."""
        return self.history[-limit:] if self.history else []
    
    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """토큰 수에 따른 비용을 추정합니다."""
        # Gemini 2.0 Flash 기준 (2024년)
        # Input: $0.000075 / 1K tokens
        # Output: $0.0003 / 1K tokens
        
        input_cost = (tokens_input / 1000) * 0.000075
        output_cost = (tokens_output / 1000) * 0.0003
        
        return round(input_cost + output_cost, 6)

# 전역 인스턴스
usage_tracker = UsageTracker()
