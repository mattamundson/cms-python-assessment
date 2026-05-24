@echo off
echo Starting Jarvis Dashboard and ngrok tunnel...
cd "C:\Users\mattm\Documents\cms-python-assessment"
start /b python dashboard.py
start /b ngrok http --domain=perioecic-piper-postsigmoid.ngrok-free.dev 9000
echo Waiting for services to initialize...
timeout /t 5
start http://localhost:9000
echo Jarvis is live at http://localhost:9000
