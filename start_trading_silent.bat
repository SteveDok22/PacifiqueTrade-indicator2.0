@echo off
cd /d "C:\Users\name\Desktop\All IN\Code Inst. Projects\PacifiqueTrade-indicator2.0"
call venv\Scripts\activate.bat
python main.py --schedule >> logs\system.log 2>&1
