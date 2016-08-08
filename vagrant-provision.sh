#!/bin/bash

APT_REGION="au"
PYTHON_VERSION="3.5.2"

set -ex

# Fix up permissions of this file because Vagrant gets them wrong
cat << BASHHISTORYEOF >> .bashrc
test -f ~/.bash_history && sudo chown vagrant: ~/.bash_history
BASHHISTORYEOF
if ! grep -q "${APT_REGION}.archive" /etc/apt/sources.list ; then
  sudo sed -i'.bak' -e "s/archive/${APT_REGION}.archive/" /etc/apt/sources.list
fi
# Only run apt-get update every 22hrs
if [ "$(($(date +%s) - $(stat -c %Z /var/lib/apt/periodic/update-success-stamp)))" -ge 79200 ]; then
  sudo apt-get update
fi
# Remove junk installed by vagrant-vbox
sudo apt-get -y autoremove
# pyenv dependencies
sudo apt-get -y install git
# Python build dependencies
sudo apt-get -y install libbz2-dev libreadline-dev libssl-dev libsqlite3-dev
# dcss-scoreboard pip package dependencies
sudo apt-get -y install libpq-dev
# Set up nginx
if ! which nginx 2>/dev/null ; then
  sudo apt-get -y install nginx
  cat << NGINXEOF > /tmp/nginx
server {
  listen 80 default_server;
  listen [::]:80 default_server ipv6only=on;
  root /home/vagrant/website;
  index index.html;
  access_log /var/log/nginx/access.log;
  error_log /var/log/nginx/error.log;
}
NGINXEOF
  sudo mv /tmp/nginx /etc/nginx/sites-enabled/default
  sudo /etc/init.d/nginx reload
fi
# Install pyenv
if ! which pyenv 2>/dev/null ; then
  curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
  export PATH="/home/vagrant/.pyenv/bin:$PATH"
  eval "$(pyenv init -)"
  eval "$(pyenv virtualenv-init -)"
  cat << PYENVEOF
export PATH="/home/vagrant/.pyenv/bin:\$PATH"
eval "\$(pyenv init -)"
eval "\$(pyenv virtualenv-init -)"
PYENVEOF
  # Install current Python
  pyenv install ${PYTHON_VERSION}
  pyenv local ${PYTHON_VERSION}
  pip3 install virtualenv
fi
if ! [[ -d venv ]] ; then
  virtualenv venv
  # shellcheck disable=SC1091
  . ./venv/bin/activate
  echo ". $(pwd)/venv/bin/activate" >> ~/.bashrc
fi
pip3 install -r /vagrant/requirements.txt
echo "/vagrant/loader.py --database sqlite --urlbase 'http://localhost:8080' --download-logfiles --download-servers cpo" > /home/vagrant/update-scoreboard
chmod +x /home/vagrant/update-scoreboard.sh
/home/vagrant/update-scoreboard.sh
