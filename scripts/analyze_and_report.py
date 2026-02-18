# -*- coding: utf-8 -*-
"""
광고업계 트렌드 분석 및 보고서 생성 스크립트 (v6.1 - 정제 강화)

핵심 변경:
- AdAge/Digiday 사이트 공통 문구(잡음) 강력 제거
- 학술 연구/논문 섹션 별도 유지
- 요약 길이 및 문장 완결성 로직 유지
"""

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from config import (
    TREND_CATEGORIES,
    get_today_data_dir,
    get_today_str,
    get_today_report_path,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 번역 설정
# ──────────────────────────────────────────────
try:
    from deep_translator import GoogleTranslator
    translator = GoogleTranslator(source='auto', target='ko')
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False
    logger.warning("deep-translator 미설치")


def translate(text):
    if not text or not HAS_TRANSLATOR:
        return text
    try:
        if len(text) > 4500:
            text = text[:4500]
        result = translator.translate(text)
        time.sleep(0.5)
        return result if result else text
    except Exception as e:
        logger.debug(f"번역 실패: {e}")
        return text


# ──────────────────────────────────────────────
# 원문 기사 전문 수집
# ──────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_article_fulltext(url):
    if not url: return ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")

        for tag in soup.find_all(["script", "style", "nav", "footer", "header",
                                   "aside", "iframe", "noscript", "form", "svg", "button"]):
            tag.decompose()

        body_text = ""
        article = soup.find("article")
        if article:
            body_text = article.get_text(separator="\n", strip=True)
        
        if len(body_text) < 500:
            for selector in [
                ".article-content", ".post-content", ".entry-content",
                ".story-body", ".article-body", ".content-body",
                '[itemprop="articleBody"]', ".article__body",
                "#article-body", ".node-body", ".wysiwyg"
            ]:
                el = soup.select_one(selector)
                if el:
                    body_text = el.get_text(separator="\n", strip=True)
                    if len(body_text) > 500: break
        
        if len(body_text) < 500:
            paragraphs = soup.find_all("p")
            valid_paragraphs = [
                p.get_text(strip=True) for p in paragraphs
                if len(p.get_text(strip=True)) > 40
            ]
            body_text = "\n".join(valid_paragraphs)

        # ── 잡음 텍스트 필터링 (강화됨) ──
        noise_patterns = [
            r'(?i)subscribe.*?newsletter',
            r'(?i)sign up for.*?email',
            r'(?i)get your.*?ticket',
            r'(?i)secure your spot.*?summit',
            r'(?i)digiday media buying summit.*?\.',
            r'(?i)subscribe to continue reading',
            r'(?i)subscription only',
            r'(?i)become a member',
            r'(?i)already a subscriber',
            r'(?i)read more about.*?membership',
            r'(?i)all rights reserved',
            r'(?i)copyright \d{4}',
            r'(?i)advertisement',
            r'(?i)follow us on',
            # AdAge/Digiday 특정 문구
            r'(?i)answers to common questions brands might have about the nation.*?s semiquincentennial',
            r'(?i)play them all',
            r'(?i)future of marketing briefing',
            r'(?i)latest marketing briefing',
        ]
        for pattern in noise_patterns:
            body_text = re.sub(pattern, '', body_text)

        lines = body_text.split('\n')
        clean_lines = []
        for line in lines:
            line_strip = line.strip()
            if len(line_strip) < 30: continue
            if line_strip.lower().startswith(('author:', 'by:', 'written by:', 'published:', 'source:')): continue
            # 특정 반복 문구 제거
            if "digiday media buying summit" in line_strip.lower(): continue
            if "answers to common questions brands might have" in line_strip.lower(): continue
            
            clean_lines.append(line_strip)
        
        body_text = '\n\n'.join(clean_lines)
        return body_text[:4000]

    except Exception as e:
        logger.debug(f"본문 수집 실패 ({url}): {e}")
        return ""


# ──────────────────────────────────────────────
# 상세 요약 생성
# ──────────────────────────────────────────────
def create_improved_summary(item, fulltext):
    title = item.get("title", "")
    rss_summary = item.get("summary", "")
    
    if fulltext and len(fulltext) > 300:
        source_text = fulltext[:1500]
    elif rss_summary and len(rss_summary) > 100:
        source_text = rss_summary
    else:
        source_text = f"{title}. {fulltext[:500]}" if fulltext else title

    kr_text = translate(source_text)

    # 한국어 잡음 제거
    noise_phrases = [
        "구독 전용", "뉴스레터 신청", "자리를 확보하세요", 
        "국가의 500주년에 대해 가질 수 있는 일반적인 질문에 대한 답변입니다", 
        "모두 재생해 보세요", "Digiday Media Buying Summit"
    ]
    for np in noise_phrases:
        kr_text = kr_text.replace(np, "")

    kr_text = kr_text.replace("&quot;", "'").replace("&#39;", "'").strip()
    
    sentences = re.split(r'(?<=[.?!])\s+', kr_text)
    valid_sentences = []
    seen = set()
    for s in sentences:
        s = s.strip()
        if len(s) < 10: continue
        if s in seen: continue
        if s.startswith(("202", "작성자:", "사진:", "이미지:")): continue
        seen.add(s)
        valid_sentences.append(s)
    
    summary_sentences = valid_sentences[:6]
    
    if summary_sentences:
        last_s = summary_sentences[-1]
        if not last_s.endswith(('.', '?', '!')):
            summary_sentences.pop()
            
    final_summary = ' '.join(summary_sentences)
    
    if len(final_summary) < 50:
        final_summary = translate(title) + ". (상세 내용 확인을 위해 원문을 참고하세요.)"
        
    return final_summary


# ──────────────────────────────────────────────
# 데이터 분류 및 선별
# ──────────────────────────────────────────────
TOPIC_KOREAN = {
    "AI/자동화": {"title": "AI 및 자동화 기술", "emoji": "🤖"},
    "프로그래매틱/애드테크": {"title": "프로그래매틱 & 애드테크", "emoji": "⚙️"},
    "소셜미디어": {"title": "소셜미디어 & 플랫폼", "emoji": "📱"},
    "동영상/CTV": {"title": "동영상/CTV/OTT", "emoji": "🎬"},
    "모바일": {"title": "모바일 & 앱 마케팅", "emoji": "📲"},
    "데이터/프라이버시": {"title": "데이터 & 프라이버시", "emoji": "🔒"},
    "브랜드/크리에이티브": {"title": "브랜드 & 크리에이티브", "emoji": "🎨"},
    "측정/효과": {"title": "효과 측정 & 분석", "emoji": "📊"},
    "리테일미디어": {"title": "리테일 미디어", "emoji": "🛒"},
}

def categorize_item_best(item):
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    best_cat, best_score = "기타", 0
    for category, keywords in TREND_CATEGORIES.items():
        if category == "기타": continue
        score = sum(1 for kw in keywords if kw in text)
        if category == "AI/자동화": score *= 1.5
        if score > best_score:
            best_score = score
            best_cat = category
    return best_cat


def relevance_score(item):
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    core_kw = [
        "advertis", "marketing", "media", "campaign", "brand", "consumer",
        "digital", "tech", "data", "platform", "content", "strategy", "research", "study", "analysis"
    ]
    score = sum(1 for kw in core_kw if kw in text)
    if item.get("type") == "academic": score += 3
    if "ai" in text or "gpt" in text or "generative" in text: score += 2
    return score


def select_top_items(articles, papers):
    articles_sorted = sorted(articles, key=lambda x: -relevance_score(x))
    papers_sorted = sorted(papers, key=lambda x: -relevance_score(x))
    
    final_articles = []
    source_counts = {}
    for a in articles_sorted:
        s = a.get("source", "unknown")
        if source_counts.get(s, 0) >= 3: continue
        final_articles.append(a)
        source_counts[s] = source_counts.get(s, 0) + 1
        if len(final_articles) >= 12: break # 기사 수 조금 늘림
        
    final_papers = papers_sorted[:8]
    return final_articles, final_papers


# ──────────────────────────────────────────────
# 보고서 생성
# ──────────────────────────────────────────────
def generate_report(articles, papers):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    top_articles, top_papers = select_top_items(articles, papers)
    
    detail_map = {}
    all_items = top_articles + top_papers
    logger.info(f"분석 대상: 기사 {len(top_articles)}건, 논문 {len(top_papers)}건")
    
    for idx, item in enumerate(all_items, 1):
        title = item.get("title", "")
        url = item.get("url", "")
        is_academic = (item.get("type") == "academic")
        logger.info(f"[{idx}/{len(all_items)}] 분석 중: {title[:30]}...")
        
        fulltext = ""
        if not is_academic:
            fulltext = fetch_article_fulltext(url)
        else:
            fulltext = item.get("summary", "") 
            
        summary = create_improved_summary(item, fulltext)
        detail_map[title] = summary

    categorized = {}
    for item in all_items:
        cat = categorize_item_best(item)
        categorized.setdefault(cat, []).append(item)
        
    report = f"""# 📢 주간 광고/미디어 심층 리포트

> **발행일**: {now}
> **주요 내용**: 업계 최신 뉴스 및 **핵심 학술 연구** 분석

---

## 💡 이번 주 핵심 요약 (Executive Summary)

"""
    ai_items = categorized.get("AI/자동화", [])
    if ai_items:
        top_ai = ai_items[0]
        report += f"### 🤖 AI 트렌드: {translate(top_ai.get('title'))}\n"
        report += f"{detail_map.get(top_ai.get('title'))}\n\n"
        
    papers_only = [i for i in all_items if i.get("type") == "academic"]
    if papers_only:
        top_paper = papers_only[0]
        report += f"### 📚 주목할 연구: {translate(top_paper.get('title'))}\n"
        report += f"{detail_map.get(top_paper.get('title'))}\n\n"

    report += "---\n\n"



    report += "## 📰 업계 주요 트렌드 (Industry News)\n\n"
    sorted_cats = sorted(categorized.keys(), key=lambda c: (c=="AI/자동화", len(categorized[c])), reverse=True)
    
    for cat in sorted_cats:
        items = [i for i in categorized[cat] if i.get("type") == "industry"]
        if not items: continue
        
        info = TOPIC_KOREAN.get(cat, {"title": cat, "emoji": "🔹"})
        report += f"### {info['emoji']} {info['title']}\n\n"
        
        for item in items:
            title_kr = translate(item.get("title"))
            summary_kr = detail_map.get(item.get("title"), "")
            source = item.get("source", "")
            url = item.get("url", "")
            
            report += f"**{title_kr}**\n"
            report += f"*({source})*\n\n"
            report += f"{summary_kr}\n\n"
            if url:
                report += f"[🔗 기사 원문]({url})\n\n"
        
        report += "\n"

    report += "---\n\n"

    report += "## 📚 최신 학술 연구 및 이론 (Research & Theory)\n\n"
    if papers_only:
        for p in papers_only:
            title_kr = translate(p.get("title", ""))
            summary_kr = detail_map.get(p.get("title", ""), "")
            source = p.get("source", "Academic Source")
            url = p.get("url", "")
            
            report += f"### {title_kr}\n"
            report += f"*출처: {source}*\n\n"
            if summary_kr:
                report += f"{summary_kr}\n\n"
            if url:
                report += f"[👉 논문/URL 확인]({url})\n\n"
            report += "---\n\n"
    else:
        report += "> *이번 주 수집된 주요 학술 논문이 없습니다.*\n\n"

    report += f"""---
> **[안내]** 본 보고서는 자동화된 시스템에 의해 수집 및 요약되었습니다. 상세한 내용은 반드시 원문을 참고하시기 바랍니다.
> 생성 시간: {now}
"""
    return report


def create_report():
    data_dir = get_today_data_dir()
    articles, papers = [], []
    try:
        with open(data_dir / "raw_articles.json", "r", encoding="utf-8") as f:
            articles = json.load(f)
        with open(data_dir / "raw_papers.json", "r", encoding="utf-8") as f:
            papers = json.load(f)
    except Exception as e:
        logger.error(f"데이터 로드 실패: {e}")
        return None
        
    if not articles and not papers:
        logger.warning("데이터가 없습니다.")
        return None
        
    logger.info("보고서 생성 프로세스 시작...")
    report_content = generate_report(articles, papers)
    
    report_path = get_today_report_path()
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    return str(report_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    path = create_report()
    if path: print(f"Report Created: {path}")
