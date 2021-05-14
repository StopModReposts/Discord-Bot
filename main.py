import discord
from discord.ext import commands
from discord_slash import SlashCommand
from dotenv import load_dotenv
import os
import requests
import json
import sentry_sdk
import re


# Basic setup
description = "Official StopModReposts bot"
bot = commands.Bot(command_prefix='/', description=description, intents=discord.Intents.all())
slash = SlashCommand(bot, sync_commands=True)
# 785935453719101450 TESTING
guild_ids = [463457129588850699]

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_USER = "smr-bot"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

sentry_sdk.init(
    "https://f6ae76c36eec4b6ab34ac46cba61d358@o309026.ingest.sentry.io/5583030",
    traces_sample_rate=1.0
)


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
    url = 'https://api.github.com/repos/StopModReposts/Illegal-Mod-Sites/issues'
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
        jsondata = json.loads(r.text)
        return jsondata.get("number")
    else:
        return 0

def checkissue(num):
    url = 'https://api.github.com/repos/StopModReposts/Illegal-Mod-Sites/issues/{0}'.format(num)
    r = requests.get(url)

    if r.status_code == 200:
        jsondata = json.loads(r.text)
        return r.status_code, jsondata.get("state"), jsondata.get("title")
    else:
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
    

@slash.slash(name="ping", description="Test command which returns the bot's ping", guild_ids=guild_ids)
async def ping(ctx):
  await ctx.send("Pong! Bot latency: {0}".format(bot.latency))
    

@slash.slash(name="submit", description="Submit a URL for review", guild_ids=guild_ids)
async def submit(ctx, url: str, description: str):
    url = re.search("([a-z0-9A-Z]\.)*[a-z0-9-]+\.([a-z0-9]{2,24})+(\.co\.([a-z0-9]{2,24})|\.([a-z0-9]{2,24}))*", url).group(0)
    if description == None:
        await ctx.send("Please add a description after the URL.")
    else:
        check = checklist(url)
        if check is False:
            num = createissue("New site to add: "+url, description+" *Automated Issue - submitted by "+str(ctx.author)+"*", ["addition"])
            link = "https://github.com/StopModReposts/Illegal-Mod-Sites/issues/" + str(num)
            embed=discord.Embed(title="Click here to view your issue", url=link, description="I've created a GitHub issue where you can track the progress of your request. You can also use `/status [issuenumber]` to get the status of your request.", color=0x00ff80)
            embed.set_author(name="Thanks for your report!")
            embed.add_field(name="Site", value=url, inline=True)
            embed.add_field(name="Issue Number", value=num, inline=True)
            embed.add_field(name="Description", value=description, inline=False)
            embed.set_footer(text="Submitted by {0}".format(ctx.author))
            await ctx.send(embed=embed)
        elif check is True:
            await ctx.send("**{0}** is already on our lists.".format(url))
        else:
            await ctx.send("Error with your request - {0}".format(check))


@slash.slash(name="check", description="Check if a website is already on our lists", guild_ids=guild_ids)
async def check(ctx, url: str):    
    url = re.search("([a-z0-9A-Z]\.)*[a-z0-9-]+\.([a-z0-9]{2,24})+(\.co\.([a-z0-9]{2,24})|\.([a-z0-9]{2,24}))*", url).group(0)
    check = checklist(url)
    if check is False:
        await ctx.send(":x: **{0}** is not on our list.".format(url))
    elif check is True:
        await ctx.send(":white_check_mark: **{0}** is on our list.".format(url))
    else:
        await ctx.send("Error with your request - {0}".format(check))


@slash.slash(name="status", description="Check the status of a GitHub issue", guild_ids=guild_ids)
async def status(ctx, num: int):
    code, status, title = checkissue(num)
    if code == 200:
        if status == "open":
            embed_status = "❌ Unreviewed (open)"
            embed_color = 0xff0000
        else:
            embed_status = "✅ Reviewed (closed)"
            embed_color = 0x00ff80
        link = "https://github.com/StopModReposts/Illegal-Mod-Sites/issues/" + str(num)
        embed=discord.Embed(title="Click here to view the issue", url=link, description="Here's the issue status you've requested.", color=embed_color)
        embed.set_author(name="Issue status")
        embed.add_field(name="Issue Number", value=num, inline=True)
        embed.add_field(name="Status", value=embed_status, inline=True)
        await ctx.send(embed=embed)
    elif code == 404:
        await ctx.send("This issue doesn't exist.")
    else:
        await ctx.send("Error with your request - Status code: {0}".format(code))


# Run bot
bot.run(DISCORD_TOKEN)
