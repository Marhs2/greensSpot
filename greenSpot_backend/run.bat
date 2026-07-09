@echo off
cd /d C:\Users\user\Desktop\sadfg
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause