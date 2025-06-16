from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import time
import os
import json
from config import FILLER_WORDS, IDEAL_WPM, SLOW_THRESHOLD, FAST_THRESHOLD

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 결과 저장 디렉토리
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

# 요청 모델
class TextAnalysisRequest(BaseModel):
    session_id: str = "default"
    text: str

# 분석기 클래스
class SpeechAnalyzer:
    def __init__(self):
        self.start_time = time.time()
        self.word_count = 0
        self.filler_counts = {word: 0 for word in FILLER_WORDS}
        self.all_words = []
        self.full_text = ""

    def add_text(self, text: str) -> None:
        words = text.strip().split()
        self.word_count += len(words)
        self.all_words.extend(words)
        self.full_text += " " + text.strip()
        self._count_fillers(words)

    def _count_fillers(self, words: list) -> None:
        for word in words:
            word_lower = word.lower().strip('.,!?;:')
            if word_lower in self.filler_counts:
                self.filler_counts[word_lower] += 1

    def get_analysis(self) -> dict:
        minutes = (time.time() - self.start_time) / 60
        wpm = self.word_count / minutes if minutes > 0 else 0

        used_fillers = {k: v for k, v in self.filler_counts.items() if v > 0}

        if wpm < SLOW_THRESHOLD:
            wpm_feedback = "조금 더 빠르게 말씀해보시는 건 어떨까요?"
        elif wpm > FAST_THRESHOLD:
            wpm_feedback = "조금 더 천천히, 또박또박 말씀해보세요."
        else:
            wpm_feedback = "적절한 속도로 말하고 계십니다."

        return {
            "full_text": self.full_text.strip(),
            "word_count": self.word_count,
            "wpm": round(wpm, 2),
            "wpm_feedback": wpm_feedback,
            "filler_words": used_fillers,
            "total_fillers": sum(used_fillers.values()),
            "speech_duration": round(time.time() - self.start_time, 2),
            "last_updated": datetime.now().isoformat()
        }

# 인메모리 세션 저장소
sessions = {}

# 분석 결과 저장
def save_result(session_id: str, result: dict) -> None:
    try:
        filename = f"speech_analysis_{session_id}_{int(time.time())}.json"
        filepath = os.path.join(RESULTS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"결과 저장 중 오류: {e}")

# API: 텍스트 분석
@app.post("/api/analyze")
async def analyze_text(request: TextAnalysisRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="텍스트를 입력해주세요.")

    # 세션 가져오기
    if request.session_id not in sessions:
        sessions[request.session_id] = SpeechAnalyzer()

    analyzer = sessions[request.session_id]
    analyzer.add_text(request.text)
    result = analyzer.get_analysis()

    # 파일 저장
    save_result(request.session_id, result)

    return {
        "success": True,
        "analysis": result
    }

# API: 세션 초기화
@app.post("/api/reset-session")
async def reset_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"success": True}

# API: 필러 단어 목록
@app.get("/api/filler-words")
async def get_filler_words():
    return {
        "success": True,
        "words": FILLER_WORDS
    }

# 📁 추가: 세션별 전체 분석 기록 불러오기
@app.get("/api/session-history/{session_id}")
async def get_session_history(session_id: str):
    result_files = [f for f in os.listdir(RESULTS_DIR) if f.startswith(f"speech_analysis_{session_id}_")]
    if not result_files:
        raise HTTPException(status_code=404, detail="해당 세션의 분석 기록이 없습니다.")

    history = []
    for fname in sorted(result_files):
        try:
            with open(os.path.join(RESULTS_DIR, fname), 'r', encoding='utf-8') as f:
                history.append(json.load(f))
        except:
            continue

    return {
        "success": True,
        "session_id": session_id,
        "history": history
    }
