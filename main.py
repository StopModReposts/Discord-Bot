import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import requests
import json


# Basic setup
description = "Official StopModReposts bot"
bot = commands.Bot(command_prefix='/', description=description)

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

GITHUB_USER = "smr-bot"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


# Bot functions
def checklist(url):
    try:
        r = requests.get('https://api.stopmodreposts.org/sites.txt')
    except:
        errormsg = "REQUEST FAILED"
        return errormsg

    if r.status_code == 200:
        if url in r.text:
            return True
        else:
            return False
    else:
        errormsg = "REQUEST FAILED WITH STATUS CODE " + str(r.status_code)
        return errormsg


def createissue(title, body=None, labels=None):
    '''Create an issue on github.com using the given parameters.'''
    # Our url to create issues via POST
    url = 'https://api.github.com/repos/StopModReposts/Illegal-Mod-Sites/issues'
    # Create an authenticated session to create the issue
    session = requests.Session()
    session.auth = (GITHUB_USER, GITHUB_TOKEN)
    # Create our issue
    issue = {'title': title,
             'body': body,
             'labels': labels}
    headers = {'Accept': 'application/vnd.github.v3+json'}
    # Add the issue to our repository
    r = session.post(url, json.dumps(issue), headers)
    if r.status_code == 201:
        print ('Successfully created Issue {0}'.format(title))
        jsondata = json.loads(r.text)
        print(jsondata.get("number"))
        return jsondata.get("number")
    else:
        print ('Could not create Issue {0}'.format(title))
        print ('Response:', r.content)
        return 0

def checkissue(num):
    url = 'https://api.github.com/repos/StopModReposts/Illegal-Mod-Sites/issues/{0}'.format(num)
    r = requests.get(url)

    if r.status_code == 200:
        print ('Successfully fetched Issue {0}'.format(num))
        jsondata = json.loads(r.text)
        return r.status_code, jsondata.get("state"), jsondata.get("title")
    else:
        print ('Could not create Issue {0}'.format(num))
        print ('Response:', r.content)
        return r.status_code, "N/A", "N/A"


# Bot commands
@bot.event
async def on_ready():
  guild_count = 0
  
  print("Logged in as")
  print(bot.user.name)
  print(bot.user.id)
  print("------")
  
  for guild in bot.guilds:
    print("{0} : {1}".format(guild.id, guild.name))
    guild_count = guild_count + 1
  
  await bot.change_presence(activity=discord.Game(name="on " + str(guild_count) + " servers | /help"))
  
  print("Bot is in " + str(guild_count) + " guilds")
    

@bot.command(description="Test command which returns ping time", help="Test command which returns ping time")
async def ping(ctx):
  await ctx.send("Pong! Bot latency: {0}".format(bot.latency))
    

@bot.command(description="Submit a URL for review", help="Submit a URL for review")
async def submit(ctx, url: str, *, args=None):
    if args == None:
        await ctx.send("Please add a description after the URL.")
    elif "http" in url:
        await ctx.send("Please only submit the Domain without http:// or https://.")
    else:
        check = checklist(url)
        if check is False:
            num = createissue("New site to add: "+url, args+" *Automated Issue*", ["addition"])
            link = "https://github.com/StopModReposts/Illegal-Mod-Sites/issues/" + str(num)
            await ctx.send("Your report for **{0}** has been received. I've created a GitHub issue (#{1} - <{2}>) where you can track the progress of your request. ".format(url, num, link))
        elif check is True:
            await ctx.send("**{0}** is already on our lists.".format(url))
        else:
            await ctx.send("Error with your request - {0}".format(check))


@bot.command(description="Check if a website is already on our lists", help="Check if a website is already on our lists")
async def check(ctx, url: str):
    if "http" in url:
        await ctx.send("Please only submit the Domain without http:// or https://.")
    else:
        check = checklist(url)
        if check is False:
            await ctx.send(":x: **{0}** is not on our list.".format(url))
        elif check is True:
            await ctx.send(":white_check_mark: **{0}** is on our list.".format(url))
        else:
            await ctx.send("Error with your request - {0}".format(check))


@bot.command(description="Check the status of a GitHub issue", help="Check the status of a GitHub issue")
async def status(ctx, num: int):
    code, status, title = checkissue(num)
    if code == 200:
        await ctx.send("Issue #{0} ({1}) - Status: {2}".format(num, title, status))
    else:
        await ctx.send("Error with your request - Status code: {0}".format(code))


# Run bot
bot.run(DISCORD_TOKEN)
