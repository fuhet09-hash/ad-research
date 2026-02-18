@echo off
REM ──────────────────────────────────────────────
REM 광고업계 트렌드 분석 - Windows 작업 스케줄러 등록
REM 매주 월요일 오전 9시에 자동 실행
REM ──────────────────────────────────────────────

SET SCRIPT_PATH=c:\Users\innocean\OneDrive\나의비서\ad-research\scripts\run_daily.py
SET TASK_NAME=AdResearch_WeeklyTrend

REM 기존 작업이 있으면 삭제
schtasks /Delete /TN "%TASK_NAME%" /F 2>nul

REM 매주 월요일 오전 9시에 실행되도록 등록
schtasks /Create /TN "%TASK_NAME%" /TR "python \"%SCRIPT_PATH%\"" /SC WEEKLY /D MON /ST 09:00 /F

echo.
echo ✅ 작업 스케줄러 등록 완료!
echo    작업 이름: %TASK_NAME%
echo    실행 주기: 매주 월요일 오전 9시
echo    실행 명령: python "%SCRIPT_PATH%"
echo.
echo 확인: taskschd.msc 에서 확인 가능
pause
