# 8s-DISCORD-BOT

A [Discord](https://discord.com/) bot that AUTOMATICALLY manages the community made [Splatoon](https://splatoon.nintendo.com/) gamemode, **8s.**

[TODO](TODO.md)

## Features
* Setup Command (/8s-setup)
  * Creates a Rules channel telling users how 8s is played and how to use the bot
  * Creates a category and 4 voice channels with a limit of 1 person (these are 8s-creator vc's)
  * A command to give you the role of either slayer, backline, or support is able to then be used
  * When someone joins this voice call it creates a new category in that Discord server 
  * A Lobby voice channel is created with a limit of 8 people (limit will be set to 10 once the game start to allow specs)
  * If the lobby channel becomes empty at any time that 8s session will be deleted from the server
  * The user is dragged from the creator voice channel into the lobby and Alpha (limit 5), Bravo (limit 5), and a 8s-chat is created (bot commands will only work here except the /setup command and moderation) are created
  * Trying to re run the /8s-setup command will not work unless you do /8s-deactivate which deletes your 8s generator setup for the server the command was used in along with the roles created for 8s
  * If one of the channels or the category is missing or the roles-embed is not found and you re do /clean-setup and the bot will auto delete everything it made and then re make it.
  * DO NOT MANUALLY CREATE OR RENAME CHANNELS UNDER ANY 8s CATEGORIES (SETUP AND CURRENT SESSIONS) THIS CAN BREAK YOUR SETUP (use discord channel, category and guild ids to fix this and store them in the db.)
* Game Command
  * People then use /8s-start and it will check if the lobby is full and if 2 players have the backline role, 2 players have support, and 4 have slayer in that lobby before finally starting
  * An embed with a button view is sent in the 8s-chat where you click a button whenever you want to re-shuffle teams (slayers will never be the same 2 sets in a row, backlines are always opposite teams and supports swap every shuffle)
  * When shuffling EVERYONE IS AUTOMATICALLY MOVCE TO THEIR CORRECT TEAM VC NO MANUALLY MOVING NECESSARY!!!
  * Not everyone needs to be in a vc, the only times where everyone needs to be are when you first join the vc to join the 8s. The bot will remember who was in the full lobby of 8 when the game is started and shuffle you, the embed will be edited with the new teams every shuffle in real time.
* Team Commands
  * /8s-sub allows you to swap yourself with a player by pinging them in the command (if you are the lobby host you will assign host to who you swap with)
  * /8s-end ends the game (deletes everyone from the database and deletes your 8s category in the server and all channels under it) (host only or admins)
  * Another thing to mention is whoever joins the 8s-creator vc with a limit of 1 at first will be assigned host for that session. This person is only one allowed to shuffle besides admins of the server


## Technologies

### Language
- [Python](https://github.com/python/cpython)
- [Discord.py (Python Discord API Wrapper)](https://github.com/Rapptz/discord.py)

### Database
- [PostgreSQL](https://github.com/postgres/postgres)
- [Async Client Library](https://github.com/MagicStack/asyncpg)


### DevOps / Deployment
- [Docker Compose](https://github.com/docker/compose)

Multi-Server Support
  * You can have multiple 8s sessions happening all at once in a single server!
  * In addition, you can have multiple servers using the bot all at once!
Async Database Writing for Scalability
Containerized via Docker Compose for Deployability
Fully Automatic Setup Command
Fully Automatic Team Generation
  * All players in a 8s game will be dragged to the correct team voice call automatically by the bot! No more switching voice calls and mixing up teams in Discord!