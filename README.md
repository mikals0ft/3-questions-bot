# Setup

Bot requires [Python 3](https://www.python.org/) to run.

### Install the dependencies

```sh
pip install -r requirements.txt
```
> Or you can use the setup.bat file to run this code automatically.

### Setting up the bot properties

```python
#Set the bot status below.
BotStatus = "Example Bot"

#Set your bots prefix.
Prefix = "."
```

# Discord Bot Setup
To run this locally,
- Create an application at https://discord.com/developers/applications.
- Under the app, create a Bot.
- Under Bot/Privileged Gateway Intents, enable both presence intent and server members intent.
- Add the token from the Bot page to the `BOT_TOKEN` environment variable.
```bash
export BOT_TOKEN=[bot token]
```
- Invite your bot to your test server via https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&permissions=432114318432&scope=bot, where the client id is found in your General Information page.

# How to run
The bot can be started with a python command:
```sh
python Bot.py
```
