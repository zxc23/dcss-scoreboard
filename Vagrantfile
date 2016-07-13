python_version = "3.5.2"
apt_region = "au"

Vagrant.configure(2) do |config|
config.vm.box = "ubuntu/trusty64"
config.vm.provider "virtualbox" do |v|
  v.memory = 512
  v.cpus = 2
end
config.vm.network "forwarded_port", guest: 80, host: 8080
    config.vm.provision "shell", inline: <<-SHELL
      set -ex
      if ! grep -q "#{apt_region}.archive" /etc/apt/sources.list ; then
        sudo sed -i'.bak' -e 's/archive/#{apt_region}.archive/' /etc/apt/sources.list
      fi
      sudo apt-get update
      sudo apt-get install -y git
      # Python build dependencies
      sudo apt-get install -y libbz2-dev libreadline-dev libssl-dev libsqlite3-dev
      # dcss-scoreboard pip package dependencies
      sudo apt-get install -y libpq-dev
      # Set up nginx
      if ! which nginx 2>/dev/null ; then
        sudo apt-get install nginx
        echo << EOF | sudo tee /etc/nginx/sites-enabled/default
          server {
            listen 80 default_server;
            listen [::]:80 default_server ipv6only=on;
            root /vagrant/website;
            index index.html;
          }
        EOF
        sudo /etc/init.d/nginx reload
      fi
      # Install pyenv
      if ! which pyenv 2>/dev/null ; then
        curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
        export PATH="/home/vagrant/.pyenv/bin:$PATH"
        eval "$(pyenv init -)"
        eval "$(pyenv virtualenv-init -)"
        echo << EOF >> ~/.bashrc
          export PATH="/home/vagrant/.pyenv/bin:$PATH"
          eval "$(pyenv init -)"
          eval "$(pyenv virtualenv-init -)"
        EOF
        # Install current Python
        pyenv install #{python_version}
        pyenv local #{python_version}
        pip3 install virtualenv
      fi
      if ! [[ -d venv ]] ; then
        virtualenv venv
        . ./venv/bin/activate
        echo ". $(pwd)/venv/bin/activate" >> ~/.bashrc
      fi
      pip3 install -r /vagrant/requirements.txt
      # /vagrant/loader.py --database sqlite --urlbase '/'
    SHELL
end
