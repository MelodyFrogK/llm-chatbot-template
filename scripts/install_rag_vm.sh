#!/bin/bash
set -e

sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
mkdir -p /opt/fastapi-llm-chatbot
cp -r . /opt/fastapi-llm-chatbot/

cd /opt/fastapi-llm-chatbot/rag
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

sudo cp /opt/fastapi-llm-chatbot/deploy/rag.service /etc/systemd/system/rag.service
sudo systemctl daemon-reload
sudo systemctl enable rag.service
sudo systemctl restart rag.service
echo "RAG installation completed"
