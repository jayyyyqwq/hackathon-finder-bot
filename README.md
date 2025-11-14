# Hackathon Finder Bot

This is a small project I built to help me find hackathons from different places on the internet. It runs 24x7 using GitHub Actions and sends me updates directly on Telegram. I can check hackathons any time by just typing /check in my bot chat.

The bot looks through a bunch of sites like MyGov, MeitY, Digital India, ISRO, Nvidia Developer, Meta Developer, Google Developer, Microsoft, Apple Developer, AWS Events, Kaggle, AIcrowd, Devfolio and Google News. It pulls the titles, the links and the deadlines when possible. It also removes old events so only active and upcoming hackathons show up.

Everything is written in simple Python. There are only three main files.  
bot.py handles the Telegram bot.  
scrapers.py collects data from all the websites.  
utils.py cleans and formats everything.

This is just something I made for fun because I was tired of missing cool hackathons. Now the bot does the work for me and messages me whenever there is a new one. It feels good to build something that actually runs on its own.
