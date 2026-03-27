#!/bin/bash
set -e

sudo apt update
sudo apt install -y nginx
sudo mkdir -p /var/www/chatbot
sudo cp web/index.html /var/www/chatbot/index.html
sudo cp nginx/chatbot.conf /etc/nginx/sites-available/chatbot.conf
sudo ln -sf /etc/nginx/sites-available/chatbot.conf /etc/nginx/sites-enabled/chatbot.conf
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
echo "Nginx installation completed"
