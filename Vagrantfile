Vagrant.configure(2) do |config|
config.vm.box = "ubuntu/trusty64"
config.vm.provision "shell", inline: <<-SHELL
  sudo apt-get update
  sudo apt-get install -y git make build-essential libssl-dev
  sudo apt-get install -y zlib1g-dev libbz2-dev libreadline-dev
  sudo apt-get install -y libsqlite3-dev wget curl llvm libncurses5-dev
  sudo apt-get install -y libncursesw5-dev python3-dev libmysqlclient-dev
SHELL
end
