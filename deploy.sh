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

export $(cat .env | sed 's/#.*//g' | xargs)
curl -H 'X-Rollbar-Access-Token: '${ROLLBAR_ACCESS_TOKEN} \
-X POST -d '{"environment": "production", "revision": "'"$(git rev-parse HEAD)"'"}' \
https://api.rollbar.com/api/1/deploy

echo 'Deploy finished'
