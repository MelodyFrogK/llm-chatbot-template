#!/bin/bash
set -e

sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
mkdir -p /opt/fastapi-llm-chatbot
cp -r . /opt/fastapi-llm-chatbot/

cd /opt/fastapi-llm-chatbot/fastapi-app
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

sudo cp /opt/fastapi-llm-chatbot/deploy/fastapi.service /etc/systemd/system/fastapi-chatbot.service
sudo systemctl daemon-reload
sudo systemctl enable fastapi-chatbot.service
sudo systemctl restart fastapi-chatbot.service
echo "FastAPI installation completed"
