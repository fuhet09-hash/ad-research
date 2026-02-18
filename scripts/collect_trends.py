# -*- coding: utf-8 -*-
"""
광고업계 트렌드 수집 스크립트
- RSS 피드에서 업계 뉴스/트렌드 수집
- Semantic Scholar API에서 학술 논문 검색
- arXiv API에서 프리프린트 검색
"""

import json
import time
import logging
from datetime import datetime, timedelta
from dateutil import parser as date_parser

import feedparser
import requests
import arxiv

from config import (
    RSS_FEEDS,
    SEARCH_KEYWORDS,
    SEMANTIC_SCHOLAR_API,
    SEMANTIC_SCHOLAR_FIELDS,
    SEMANTIC_SCHOLAR_LIMIT,
    ARXIV_MAX_RESULTS,
    MEDIA_FILTER_KEYWORDS,
    get_today_data_dir,
    get_today_str,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# RSS 피드 수집
# ──────────────────────────────────────────────
def collect_rss_feeds(days_back=7):
    """
    RSS 피드에서 최근 기사를 수집합니다.

    Args:
        days_back: 며칠 전까지의 기사를 수집할지 (기본 7일)

    Returns:
        list[dict]: 수집된 기사 목록
    """
    cutoff = datetime.now() - timedelta(days=days_back)
    articles = []

    for source_name, feed_url in RSS_FEEDS.items():
        logger.info(f"[RSS] {source_name} 수집 중: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo and not feed.entries:
                logger.warning(f"[RSS] {source_name} 파싱 실패: {feed.bozo_exception}")
                continue

            count = 0
            for entry in feed.entries:
                # 날짜 파싱
                pub_date = None
                for date_field in ["published", "updated", "created"]:
                    if hasattr(entry, date_field) and getattr(entry, date_field):
                        try:
                            pub_date = date_parser.parse(getattr(entry, date_field))
                            # timezone-naive로 변환
                            if pub_date.tzinfo:
                                pub_date = pub_date.replace(tzinfo=None)
                            break
                        except (ValueError, TypeError):
                            continue

                # 날짜 필터링
                if pub_date and pub_date < cutoff:
                    continue

                # 기사 정보 추출
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()

                # HTML 태그 간단 제거
                import re
                summary = re.sub(r"<[^>]+>", "", summary).strip()

                if not title:
                    continue

                articles.append({
                    "source": source_name,
                    "type": "industry",
                    "title": title,
                    "url": link,
                    "summary": summary[:1000],  # 요약 길이 제한
                    "published_date": pub_date.isoformat() if pub_date else None,
                    "authors": entry.get("author", ""),
                })
                count += 1

            logger.info(f"[RSS] {source_name}: {count}건 수집")

        except Exception as e:
            logger.error(f"[RSS] {source_name} 오류: {e}")

    logger.info(f"[RSS] 총 {len(articles)}건 수집 완료")
    return articles


# ──────────────────────────────────────────────
# Semantic Scholar 검색
# ──────────────────────────────────────────────
def search_semantic_scholar(days_back=30):
    """
    Semantic Scholar API로 광고/미디어 관련 최신 논문을 검색합니다.

    Args:
        days_back: 며칠 이내 출판된 논문 검색 (기본 30일)

    Returns:
        list[dict]: 검색된 논문 목록
    """
    papers = []
    seen_titles = set()
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    for keyword in SEARCH_KEYWORDS[:5]:  # 상위 5개 키워드만 (API 제한 고려)
        logger.info(f"[Semantic Scholar] 검색: {keyword}")
        try:
            params = {
                "query": keyword,
                "fields": SEMANTIC_SCHOLAR_FIELDS,
                "limit": SEMANTIC_SCHOLAR_LIMIT,
                "publicationDateOrYear": f"{cutoff_date}:",
            }
            resp = requests.get(SEMANTIC_SCHOLAR_API, params=params, timeout=15)

            if resp.status_code == 429:
                logger.warning("[Semantic Scholar] Rate limit. 5초 대기...")
                time.sleep(5)
                resp = requests.get(SEMANTIC_SCHOLAR_API, params=params, timeout=15)

            if resp.status_code != 200:
                logger.warning(f"[Semantic Scholar] HTTP {resp.status_code}")
                continue

            data = resp.json()
            for paper in data.get("data", []):
                title = paper.get("title", "").strip()
                if not title or title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())

                authors = ", ".join(
                    a.get("name", "") for a in paper.get("authors", [])[:5]
                )

                # DOI 또는 URL
                ext_ids = paper.get("externalIds", {}) or {}
                doi = ext_ids.get("DOI", "")
                url = paper.get("url", "")
                if doi and not url:
                    url = f"https://doi.org/{doi}"

                papers.append({
                    "source": "Semantic Scholar",
                    "type": "academic",
                    "title": title,
                    "url": url,
                    "summary": (paper.get("abstract") or "")[:1500],
                    "published_date": paper.get("publicationDate"),
                    "authors": authors,
                    "year": paper.get("year"),
                    "citations": paper.get("citationCount", 0),
                    "keyword": keyword,
                })

            time.sleep(1)  # API rate limit 준수

        except Exception as e:
            logger.error(f"[Semantic Scholar] 오류 ({keyword}): {e}")

    logger.info(f"[Semantic Scholar] 총 {len(papers)}건 검색 완료")
    return papers


# ──────────────────────────────────────────────
# arXiv 검색
# ──────────────────────────────────────────────
def search_arxiv(days_back=30):
    """
    arXiv에서 광고/미디어 관련 최신 논문을 검색합니다.

    Returns:
        list[dict]: 검색된 논문 목록
    """
    papers = []
    seen_titles = set()

    search_queries = [
        "advertising media",
        "digital advertising",
        "ad technology",
        "programmatic advertising",
        "social media marketing",
    ]

    for query in search_queries:
        logger.info(f"[arXiv] 검색: {query}")
        try:
            search = arxiv.Search(
                query=query,
                max_results=ARXIV_MAX_RESULTS,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )

            client = arxiv.Client()
            for result in client.results(search):
                title = result.title.strip()
                if title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())

                authors = ", ".join(a.name for a in result.authors[:5])
                pub_date = result.published

                papers.append({
                    "source": "arXiv",
                    "type": "academic",
                    "title": title,
                    "url": result.entry_id,
                    "summary": (result.summary or "")[:1500],
                    "published_date": pub_date.strftime("%Y-%m-%d") if pub_date else None,
                    "authors": authors,
                    "categories": [c for c in result.categories],
                })

            time.sleep(1)

        except Exception as e:
            logger.error(f"[arXiv] 오류 ({query}): {e}")

    logger.info(f"[arXiv] 총 {len(papers)}건 검색 완료")
    return papers


# ──────────────────────────────────────────────
# 중복 제거
# ──────────────────────────────────────────────
def deduplicate(items):
    """제목 기반으로 중복 항목 제거"""
    seen = set()
    unique = []
    for item in items:
        title_key = item["title"].lower().strip()
        # 짧은 제목은 건너뛰기
        if len(title_key) < 10:
            continue
        if title_key not in seen:
            seen.add(title_key)
            unique.append(item)
    return unique


# ──────────────────────────────────────────────
# 메인 수집 함수
# ──────────────────────────────────────────────
def collect_all():
    """
    모든 소스에서 데이터를 수집하고 저장합니다.

    Returns:
        dict: {"articles": [...], "papers": [...]}
    """
    logger.info("=" * 60)
    logger.info(f"광고업계 트렌드 수집 시작: {get_today_str()}")
    logger.info("=" * 60)

    # 1) RSS 피드에서 업계 기사 수집
    articles = collect_rss_feeds(days_back=7)

    # 2) Semantic Scholar에서 학술 논문 검색
    ss_papers = search_semantic_scholar(days_back=30)

    # 3) arXiv에서 프리프린트 검색
    arxiv_papers = search_arxiv(days_back=30)

    # 4) 학술 논문 통합 & 중복 제거
    all_papers = deduplicate(ss_papers + arxiv_papers)

    # 5) 저장
    data_dir = get_today_data_dir()

    articles_path = data_dir / "raw_articles.json"
    with open(articles_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    logger.info(f"업계 기사 저장: {articles_path} ({len(articles)}건)")

    papers_path = data_dir / "raw_papers.json"
    with open(papers_path, "w", encoding="utf-8") as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=2)
    logger.info(f"학술 논문 저장: {papers_path} ({len(all_papers)}건)")

    # 통합 데이터
    all_items = articles + all_papers
    trends_path = data_dir / "trends.json"
    with open(trends_path, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    logger.info(f"통합 데이터 저장: {trends_path} ({len(all_items)}건)")

    return {"articles": articles, "papers": all_papers}


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    result = collect_all()
    print(f"\n✅ 수집 완료: 업계 기사 {len(result['articles'])}건, 학술 논문 {len(result['papers'])}건")
