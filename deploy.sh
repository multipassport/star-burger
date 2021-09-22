#!/bin/bash

git pull

source /opt/star-burger/env/bin/activate

pip install -r requirements.txt

sudo curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

sudo npm install --dev
sudo npm install -g parcel@latest

/opt/star-burger/env/bin/python manage.py collectstatic --noinput

sudo systemctl reload starburger
sudo systemctl reload nginx

echo 'Deploy finished'
