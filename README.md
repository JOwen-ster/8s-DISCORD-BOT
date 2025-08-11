# 8s-DISCORD-BOT

A Discord bot that manages Splatoon 8s.

[TODO](TODO.md)

## Features
* Setup Command (/8s-enable)
  * Creates a category and 4 voice channels with a limit of 1 person (these are 8s-creator vc's)
  * A new channel called 8s-game-roles is also created where a dropdown view is sent to select if you are slayer, backline, or support
  * When someone joins this voice call it creates a new category in the Discord called 8s-Discord_user_id
  * A Lobby voice channel is created with a limit of 8 people (limit will be set to 10 once the game start to allow specs)
  * If the lobby channel becomes empty at any time that 8s session will be deleted from the server and taken out of the bots database.
  * The user is dragged from the creator voice channel into the lobby voice channel and once 7 more people join, Alpha (limit 5), Bravo (limit 5), and a 8s-chat is created (bot commands will only work here except the /setup command and moderation)
  * Trying to re run the /8s-enable command will not work unless you do /8s-disable which deletes all 8s related channels from your server and the database
  * If one of the channels or the category is missing or the roles-embed is not found and you re do /setup the bot will auto disable since your current setup isnt valid and prompt you to run /enable again 
  * DO NOT MANUALLY CREATE OR RENAME CHANNELS UNDER ANY 8s CATEGORIES (SETUP AND CURRENT SESSIONS) THIS CAN BREAK YOUR SETUP (use discord channel and category ids to fix this and store them in the db.
* Game Command
  * People then use /8s-start and it will check if the lobby is full and if 2 players have the backline role, 2 players have support, and 4 have slayer in that lobby before finally starting
  * An embed with a button view is sent in the 8s-chat where you click a button whenever you want to re-shuffle teams (slayers will never be the same 2 sets in a row, backlines are always opposite teams and supports swap every shuffle)
  * When shuffling EVERYONE IS AUTOMATICALLY MOVCE TO THEIR CORRECT TEAM VC NO MANUALLY MOVING NECESSARY!!!
  * Not everyone needs to be in a vc, the only times where everyone needs to be are when you first join the vc to join the 8s. The bot will remember who was in the full lobby of 8 when the game is started and shuffle you, the embed will be edited with the new teams every shuffle in real time.
* Team Commands
  * /8s-sub allows you to swap yourself with a player by pinging them in the command (if you are the lobby host you will assign host to who you swap with)
  * /8s-end ends the game (deletes everyone from the database and deletes your 8s category in the server and all channels under it) (host only or admins)
  * Another thing to mention is whoever joins the 8s-creator vc with a limit of 1 at first will be assigned host for that session. This person is only one allowed to shuffle besides admins of the server

# If every voice channel is empty for your 8s category, the game will be deleted and removed. You will have to re host by joinin the creator again
  

## Technologies
- Python 3.12
- Discord.py
- PostgreSQL
- Docker (compose)

