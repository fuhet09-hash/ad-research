# -*- coding: utf-8 -*-
"""
이메일 발송 스크립트
- 마크다운 보고서를 HTML로 변환하여 이메일 발송
- Gmail SMTP 사용
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import markdown

from config import (
    EMAIL_SENDER,
    EMAIL_RECIPIENT,
    EMAIL_SUBJECT_PREFIX,
    GMAIL_SMTP_SERVER,
    GMAIL_SMTP_PORT,
    GMAIL_APP_PASSWORD,
    get_today_str,
    get_today_report_path,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# HTML 이메일 템플릿
# ──────────────────────────────────────────────
EMAIL_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: 'Segoe UI', 'Apple SD Gothic Neo', '맑은 고딕', sans-serif;
        line-height: 1.8;
        color: #333;
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f8f9fa;
    }}
    .container {{
        background-color: #fff;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    h1 {{
        color: #1a73e8;
        border-bottom: 3px solid #1a73e8;
        padding-bottom: 12px;
        font-size: 24px;
    }}
    h2 {{
        color: #333;
        margin-top: 30px;
        padding-bottom: 8px;
        border-bottom: 1px solid #e0e0e0;
    }}
    h3 {{
        color: #555;
        margin-top: 20px;
    }}
    h4 {{
        color: #1a73e8;
        margin-top: 15px;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 15px 0;
    }}
    th, td {{
        border: 1px solid #ddd;
        padding: 10px 14px;
        text-align: left;
    }}
    th {{
        background-color: #1a73e8;
        color: white;
        font-weight: 600;
    }}
    tr:nth-child(even) {{
        background-color: #f2f6fc;
    }}
    blockquote {{
        border-left: 4px solid #1a73e8;
        margin: 10px 0;
        padding: 8px 16px;
        background-color: #f8f9fa;
        color: #555;
        font-size: 14px;
    }}
    a {{
        color: #1a73e8;
        text-decoration: none;
    }}
    a:hover {{
        text-decoration: underline;
    }}
    hr {{
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 20px 0;
    }}
    strong {{
        color: #333;
    }}
    .footer {{
        margin-top: 30px;
        padding-top: 15px;
        border-top: 1px solid #e0e0e0;
        color: #888;
        font-size: 12px;
    }}
</style>
</head>
<body>
<div class="container">
{content}
</div>
<div class="footer">
    <p>이 이메일은 광고업계 트렌드 분석 시스템에서 자동 발송되었습니다.</p>
</div>
</body>
</html>
"""


def markdown_to_html(md_content):
    """마크다운을 HTML로 변환"""
    html = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "nl2br"],
    )
    return EMAIL_HTML_TEMPLATE.format(content=html)


def send_report_email(report_path=None):
    """
    보고서를 이메일로 발송합니다.

    Args:
        report_path: 보고서 파일 경로 (None이면 오늘 날짜 보고서 사용)

    Returns:
        bool: 발송 성공 여부
    """
    # 보고서 파일 확인
    if report_path is None:
        report_path = get_today_report_path()
    else:
        report_path = Path(report_path)

    if not report_path.exists():
        logger.error(f"보고서 파일을 찾을 수 없습니다: {report_path}")
        return False

    # 보고서 읽기
    with open(report_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Gmail 앱 비밀번호 확인
    if not GMAIL_APP_PASSWORD:
        logger.error(
            "GMAIL_APP_PASSWORD 환경변수가 설정되지 않았습니다.\n"
            "다음 명령으로 설정하세요:\n"
            '  set GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx\n'
            "\n"
            "Google 앱 비밀번호 생성: https://myaccount.google.com/apppasswords"
        )
        logger.info(f"보고서는 파일로 저장되었습니다: {report_path}")
        return False

    # HTML 변환
    html_content = markdown_to_html(md_content)

    # 이메일 구성
    today = get_today_str()
    subject = f"{EMAIL_SUBJECT_PREFIX} {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT

    # 텍스트 + HTML 버전
    text_part = MIMEText(md_content, "plain", "utf-8")
    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(text_part)
    msg.attach(html_part)

    # 발송
    try:
        logger.info(f"이메일 발송 중... ({EMAIL_SENDER} → {EMAIL_RECIPIENT})")

        with smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

        logger.info(f"✅ 이메일 발송 완료: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail 인증 실패. 앱 비밀번호를 확인하세요.\n"
            "1. 2단계 인증이 활성화되어 있는지 확인\n"
            "2. 앱 비밀번호가 올바른지 확인\n"
            "생성: https://myaccount.google.com/apppasswords"
        )
        return False

    except Exception as e:
        logger.error(f"이메일 발송 실패: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    success = send_report_email()
    if success:
        print("\n✅ 이메일 발송 완료!")
    else:
        print("\n⚠️ 이메일 발송 실패 - 보고서는 파일로 저장되었습니다.")
