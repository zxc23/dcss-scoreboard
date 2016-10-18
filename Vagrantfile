Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.provider "virtualbox" do |v|
    v.memory = 512
    v.cpus = 1
  end
  config.vm.provider "docker" do |d|
    d.build_dir = "."
  end
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.provision "shell", path: "vagrant-provision.sh", privileged: false
end
