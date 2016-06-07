## DCSS Scoreboard

A bundle of scripts to create a scoreboard website for DCSS.

## Why make another scoreboard?

- The CAO scoreboard is old; |amethyst said 1.3 people understood it and fewer still had time for working on it. So we decided to start from scratch.
- Faster scripts. No benchmarks just yet so you'll have to take our word for it.
- Better streaks:
  - Streak griefers are detected with some clever heuristics and blacklisted from the stats.
  - To extend your streak you must start the next game after finishing the previous one. No more queuing up games and winning them all at once for a streak!
- Bots are blacklisted so the min-duration leaderboard is finally useful again!
- It’s time for a fresh new UI. New features include player search and a fancy new logo by Ontoclasm. Plus, we’re probably improving stuff as you read this.
- Per-player tracking of many stats. We hope you like stats.
- New improvements arriving all the time. If you like, you can even [help out](https://github.com/zxc23/dcss-scoreboard).

## How to use

Python 3.5 is required. Install pre-requisites with `pip install -r requirements.txt`.

For testing purposes, you can download lots of logfiles with `download-logs.sh`.

Once you have some logfiles, you can run `loader.py`, which is a simple test script that:

1. Loads all these log files into the database
2. Runs scoring on every log line in the database
3. Writes website pages out based on this data

The sqlite database is `scoredata.db` and the website is written to `dcss-scoreboard-html/`.

## Windows users

1. First, get Vagrant at https://www.vagrantup.com/ and install it.
2. Install the vbguest plugin with `vagrant plugin install vagrant-vbguest`.
3. Next, open in the git folder in cmd which should contain 'Vagrantfile', and run `vagrant up`. This will set up an Ubuntu VM and might take a while.
4. Next, `vagrant ssh` to ssh into the VM and run `bash /vagrant/setup1.sh`.
5. Exit with ctrl-d and reopen with `vagrant ssh`. Run `bash /vagrant/setup2.sh` but be aware this can take a while.
6. Open scoreboard/constants.py and change the line `WEBSITE_URLBASE = os.path.join(os.getcwd(), WEBSITE_DIR)` to point to a 'website' folder in your current directory, e.g. `WEBSITE_URLBASE = 'D:\David\Documents\DCSS Scoreboard\website'`.
7. `cd /vagrant` and `python loader.py` will start the scripts.
8. Ctrl-D will exit out of the VM's terminal. `vagrant halt` will shut down the VM when you're done. `vagrant up` will start it up again when you need it, and `vagrant destroy` will remove the VM entirely.

## Logfile locations

You can find current logfile locations in Sequell's source files: https://github.com/crawl/sequell/blob/master/config/sources.yml

## Development

You can see development status here: https://trello.com/b/9Nija4jC/dcss-scoreboard
