Vagrant.configure(2) do |config|
config.vm.box = "ubuntu/trusty64"
config.vm.provision "shell", inline: <<-SHELL
  ln -s /vagrant /home/vagrant
  sudo apt-get update
  sudo apt-get install -y git make build-essential libssl-dev \ 
  zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget \
  curl llvm libncurses5-dev libncursesw5-dev python3-dev \
  libmysqlclient-dev
  curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
  echo 'export PATH="/home/vagrant/.pyenv/bin:$PATH"' >>~/.bash_profile
  echo 'eval "$(pyenv init -)"' >>~/.bash_profile
  echo 'eval "$(pyenv virtualenv-init -)"' >>~/.bash_profile
  pyenv install 3.5.1
  pyenv global 3.5.1
  pip install -r /vagrant/requirements.txt
SHELL
end
