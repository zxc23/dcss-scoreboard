## DCSS Scoreboard

Generate scoring website for DCSS.

## How to use

Install pre-requisites with `pip install -r requirements.txt`.

For testing purposes, you can download lots of logfiles with `download-logs.sh`.

Once you have some logfiles, you can run `loader.py`, which is a simple test script that:

1. Loads all these log files into the database
2. Runs scoring on every log line in the database
3. Writes website pages out based on this data

The sqlite database is `scoredata.db` and the website is written to `dcss-scoreboard-html/`.

## Logfile locations

You can find current logfile locations in Sequell's source files: https://github.com/crawl/sequell/blob/master/config/sources.yml

## Development

You can see development status here: https://docs.google.com/document/d/1gTOGx1CVllpWclRsvBFIFOGJrT9z_0Pvmjk4PLoh7cs/edit?usp=sharing

## Setting up a development environment using Vagrant

1. First, get Vagrant at https://www.vagrantup.com/ and install it.
2. Next, cd to the git repository which should contain 'Vagrantfile', and run 'vagrant up'. This will set things up and might take a while.
3. Open scoreboard/constants.py and change the line 'WEBSITE_URLBASE = os.path.join(os.getcwd(), WEBSITE_DIR)' to point to a 'website' folder in your current directory. E.g. "WEBSITE_URLBASE = 'D:\David\Documents\DCSS Scoreboard\website'".
4. To run the scripts, do 'vagrant ssh' which will open a terminal in the VM and 'cd vagrant'. Finally, 'python loader.py' will start the scripts.
