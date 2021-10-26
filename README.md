# A Link to the Past Randomzier Discrod Bot a.k.a. catfishbot

## Description

This bot was mainly developed for the discord of a friend. We would like to use other bots (e.g. SahasralaBot, Lazy Kid), 
but they were not designed to be run easily or not free.

I mainly use the pyz3r libary and also take some ideas from the SahasralaBot. So mainly the credits go to his developer,
but I also added own ideas or also try to rebuild Lazy Kid bot, race solution for our discord.

If you like to use it, feel free to try it out, but because I am not a main developer in python, I can not guarantie that
this bot is free of bugs or easy to use.

## Operation of the bot

### Environment variables

Set environment variables / add .env file for pipenv to use or in docker-compose

- DISCORD_TOKEN / Token for you discord bot
- ALTTP_ROM / Orginal japanisch rom to generate a game / create patch files.
- (opational) LANG / Language to support help and commands in another language (e.g. de)

### Native

Download the project and install all dependencies with pipenv.

- pipenv install
- pipenv run python catfishbot.py

### Docker

Download the project

- copy the docker-compose example and adjust the file
- docker-compose up -d --build


