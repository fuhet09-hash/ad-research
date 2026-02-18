# -*- coding: utf-8 -*-
"""
광고업계 트렌드 분석 - 메인 파이프라인
전체 프로세스를 순서대로 실행합니다:
  1. 트렌드/논문 수집
  2. 분석 및 보고서 생성
  3. 이메일 발송
"""

import sys
import io
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Windows 콘솔 인코딩 문제 해결 (이모지/한국어 출력)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 스크립트 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent))

from collect_trends import collect_all
from analyze_and_report import create_report
from send_email import send_report_email
from config import get_today_str

logger = logging.getLogger("ad_research")


def run_pipeline(skip_email=False):
    """
    전체 파이프라인을 실행합니다.

    Args:
        skip_email: True이면 이메일 발송을 건너뜁니다.
    """
    start_time = datetime.now()
    today = get_today_str()

    print("=" * 60)
    print(f"  📢 광고업계 트렌드 분석 파이프라인")
    print(f"  📅 실행 날짜: {today}")
    print("=" * 60)
    print()

    # ── Step 1: 트렌드/논문 수집 ──
    print("📥 [1/3] 트렌드 및 논문 수집 중...")
    try:
        result = collect_all()
        n_articles = len(result["articles"])
        n_papers = len(result["papers"])
        print(f"   ✅ 업계 기사: {n_articles}건, 학술 논문: {n_papers}건 수집 완료")
    except Exception as e:
        logger.error(f"수집 실패: {e}")
        print(f"   ❌ 수집 실패: {e}")
        return False

    print()

    # ── Step 2: 분석 & 보고서 생성 ──
    print("📊 [2/3] 분석 및 보고서 생성 중...")
    try:
        report_path = create_report()
        if report_path:
            print(f"   ✅ 보고서 생성 완료: {report_path}")
        else:
            print("   ⚠️ 생성할 데이터가 없습니다.")
            return False
    except Exception as e:
        logger.error(f"보고서 생성 실패: {e}")
        print(f"   ❌ 보고서 생성 실패: {e}")
        return False

    print()

    # ── Step 3: 이메일 발송 ──
    if skip_email:
        print("📧 [3/3] 이메일 발송 건너뜀 (--no-email 옵션)")
    else:
        print("📧 [3/3] 이메일 발송 중...")
        try:
            success = send_report_email(report_path)
            if success:
                print("   ✅ 이메일 발송 완료!")
            else:
                print("   ⚠️ 이메일 발송 실패 - 보고서는 파일로 저장됨")
        except Exception as e:
            logger.error(f"이메일 발송 실패: {e}")
            print(f"   ⚠️ 이메일 발송 실패: {e}")

    # ── 완료 ──
    elapsed = (datetime.now() - start_time).seconds
    print()
    print("=" * 60)
    print(f"  🏁 파이프라인 완료 (소요 시간: {elapsed}초)")
    print(f"  📄 보고서: {report_path}")
    print("=" * 60)

    return True


def main():
    parser = argparse.ArgumentParser(
        description="광고업계 트렌드 분석 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python run_daily.py              # 전체 실행 (수집 + 보고서 + 이메일)
  python run_daily.py --no-email   # 이메일 없이 실행
  python run_daily.py --debug      # 디버그 모드
        """,
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="이메일 발송을 건너뜁니다",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="디버그 로그를 출력합니다",
    )

    args = parser.parse_args()

    # 로깅 설정
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # 실행
    success = run_pipeline(skip_email=args.no_email)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
