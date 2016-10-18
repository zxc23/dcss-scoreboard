# DCSS Scoreboard

Tool to create a scoreboard for online DCSS games.

[![Code Climate](https://codeclimate.com/github/zxc23/dcss-scoreboard/badges/gpa.svg)](https://codeclimate.com/github/zxc23/dcss-scoreboard)
[![Build Status](https://travis-ci.org/zxc23/dcss-scoreboard.svg?branch=master)](https://travis-ci.org/zxc23/dcss-scoreboard)

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

## High-level program flow

1. `loader.py`: CLI entrypoint
  1. `sources.py`: download logfiles in parallel using `wget --continue`
  1. `log_import.py`: load each game (eg each line) from logfiles into the database
  1. `scoring.py`: score each unscored game:
    1. Handle streaks
  1. `write_website.py`: create the website directory
    1. Write all global pages (index, highscores, streaks)
    1. Write pages for players with newly scored games

## How to use

Python 3.5+ is required. Install pre-requisites with `pip install -r requirements.txt`. If you want to use Postgres as your database server, also install the `psycopg2` pip module (which requires `libpq-dev` on Ubuntu).

To use the code, run `loader.py --help`.

## Windows users

1. First, get Vagrant at <https://www.vagrantup.com/> and install it.
1. Install the vbguest plugin with `vagrant plugin install vagrant-vbguest`.
1. Open in the git folder in cmd which should contain 'Vagrantfile', and run `vagrant up`. This will set up an Ubuntu VM and might take a while.
1. Once the setup is complete, you should be able to visit <http://localhost:8080/> in a web browser and see your development website!
1. To update your development scoreboard, you can SSH into the machine with `vagrant ssh` and run `./update-scoreboard.sh`.
1. Ctrl-D will exit out of the VM's terminal. `vagrant halt` will shut down the VM when you're done. `vagrant up` will start it up again when you need it, and `vagrant destroy` will remove the VM entirely.

Altrnatively, specify port 8000 when writing the website, `cd /vagrant` and `python server.py &` to start serving the website at <http://localhost:8000/>.

## Postgresql Management

To create a user and database in Postgres, try the following commands:

```bash
sudo -u postgres createuser -D -A -P scoreboard
sudo -u postgres createdb -O scoreboard scoreboard
```

## Development

You can see development status here: <https://trello.com/b/9Nija4jC/dcss-scoreboard>.
