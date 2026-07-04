 

 
sudo apt update && sudo apt upgrade -y

 
sudo apt install -y python3 python3-pip python3-venv git

 
sudo apt install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2

 
python3 -m venv venv
source venv/bin/activate

 
pip install -r requirements.txt

 
playwright install chromium

 
CRON_JOB="0 3 * * * cd $(pwd) && $(pwd)/venv/bin/python $(pwd)/src/main.py >> $(pwd)/logs/cron.log 2>&1"
( crontab -l | grep -v -F "$(pwd)/src/main.py" ; echo "$CRON_JOB" ) | crontab -

echo "Deployment complete. Cron installed."