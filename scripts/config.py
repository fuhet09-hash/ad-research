# -*- coding: utf-8 -*-
"""
광고업계 트렌드 분석 워크플로우 - 설정 파일
"""

import os
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────
# 프로젝트 경로
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

def get_today_str():
    """오늘 날짜 문자열 반환 (YYYY-MM-DD)"""
    return datetime.now().strftime("%Y-%m-%d")

def get_today_data_dir():
    """오늘 날짜 데이터 디렉토리 (자동 생성)"""
    d = DATA_DIR / get_today_str()
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_today_report_path():
    """오늘 날짜 보고서 파일 경로"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR / f"{get_today_str()}_report.md"

# ──────────────────────────────────────────────
# RSS 피드 소스 (광고/미디어 업계)
# ──────────────────────────────────────────────
RSS_FEEDS = {
    # 🌍 해외 (Global)
    "AdAge": "https://adage.com/arc/outboundfeeds/rss/",
    "Adweek": "https://www.adweek.com/feed/",
    "The Drum": "https://www.thedrum.com/search?refinementList%5Bcontent_type%5D%5B0%5D=article&query=marketing&format=rss", # 대체 URL 시도
    "Marketing Dive": "https://www.marketingdive.com/feeds/news/",
    "Digiday": "https://digiday.com/feed/",
    "MediaPost": "https://www.mediapost.com/rss/MediapostMediaDailyNews/", # 보다 안정적인 채널로 변경
    
    # 🇰🇷 국내 (Korea)
    "매드타임스": "http://www.madtimes.org/rss/allArticle.xml", # (이후 collect_trends.py에서 헤더 추가로 해결)
    "모비인사이드": "https://mobiinside.co.kr/feed/",
    "블로터": "https://www.bloter.net/rss/allArticle.xml",
    "아주경제(광고)": "https://www.ajunews.com/rss/040106",
}

# ──────────────────────────────────────────────
# AI 분석 API 키 (택 1, 환경 변수)
# ──────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ──────────────────────────────────────────────
# 학술 검색 키워드
# ──────────────────────────────────────────────
SEARCH_KEYWORDS = [
    "advertising media effectiveness",
    "digital advertising technology",
    "programmatic advertising",
    "social media advertising",
    "video advertising",
    "mobile advertising",
    "advertising measurement",
    "media planning optimization",
    "brand advertising strategy",
    "ad tech innovation",
]

# Semantic Scholar 설정
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_FIELDS = "title,authors,abstract,url,year,citationCount,publicationDate,externalIds"
SEMANTIC_SCHOLAR_LIMIT = 10  # 키워드당 최대 결과 수

# arXiv 설정
ARXIV_MAX_RESULTS = 10  # 키워드당 최대 결과 수

# ──────────────────────────────────────────────
# 이메일 설정
# ──────────────────────────────────────────────
EMAIL_SENDER = "fuhet09@gmail.com"
EMAIL_RECIPIENT = "hyungu@innocean.com"
EMAIL_SUBJECT_PREFIX = "[광고 트렌드 리포트]"
GMAIL_SMTP_SERVER = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

# Gmail 앱 비밀번호 (환경변수에서 읽기)
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# ──────────────────────────────────────────────
# 트렌드 주제 분류 카테고리
# ──────────────────────────────────────────────
TREND_CATEGORIES = {
    "AI/자동화": ["ai", "artificial intelligence", "machine learning", "automation", "generative", "chatgpt", "llm"],
    "프로그래매틱/애드테크": ["programmatic", "ad tech", "adtech", "rtb", "real-time bidding", "dsp", "ssp"],
    "소셜미디어": ["social media", "instagram", "tiktok", "facebook", "meta", "youtube", "influencer", "creator"],
    "동영상/CTV": ["video", "ctv", "connected tv", "streaming", "ott", "youtube"],
    "모바일": ["mobile", "app", "in-app", "smartphone"],
    "데이터/프라이버시": ["data", "privacy", "cookie", "cookieless", "first-party", "gdpr", "consent"],
    "브랜드/크리에이티브": ["brand", "creative", "campaign", "storytelling", "content marketing"],
    "측정/효과": ["measurement", "roi", "attribution", "effectiveness", "kpi", "analytics"],
    "리테일미디어": ["retail media", "commerce media", "amazon ads", "walmart"],
    "기타": [],
}

# ──────────────────────────────────────────────
# 기사/논문 필터링 키워드 (미디어/매체 관련)
# ──────────────────────────────────────────────
MEDIA_FILTER_KEYWORDS = [
    "advertising", "ad", "ads", "media", "programmatic", "campaign",
    "brand", "marketing", "digital", "creative", "agency", "advertiser",
    "publisher", "impression", "reach", "audience", "targeting",
    "video", "display", "social", "mobile", "ctv", "streaming",
    "measurement", "attribution", "roi", "effectiveness",
    "ad tech", "adtech", "platform", "google ads", "meta ads",
]
