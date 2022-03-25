import discord, os, requests, json, sentry_sdk, json, re, time, asyncio
from discord.ext import commands
from discord_slash import SlashCommand
from dotenv import load_dotenv

# to do :
# multi ban
#cogs[wip]



#cogs
@bot.command()
async def load(ctx, extention):
    client.load_extention(f'cogs.{extention}')

@bot.command()
async def load(ctx, extention):
    client.unload_extention(f'cogs.{extention}')

for filename in os.lisrdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extention(f'cogs.{filename[:-3]}')

#logging
async def update_stats():
    await client.wait_until_ready()
    global messages, joined

    while not client.is_closed():
        try:
            with open("stats.txt", "a") as f:
                f.write(f"Time: {int(time.time())}, Messages: {messages}, Members Joined: {joined}\n")

            messages = 0
            joined = 0

            await asyncio.sleep(5)
        except Exception as e:
            print(e)
            await asyncio.sleep(5)


# Basic setup
description = "Official StopModReposts bot"
bot = commands.Bot(command_prefix='/', description=description, intents=discord.Intents.all())
slash = SlashCommand(bot, sync_commands=True)
# 785935453719101450 TESTING
guild_ids = [463457129588850699]
bot.warnings = {} # guild_id : {member_id: [count, [(admin_id, reason)]]}

if os.path.exists(os.getcwd() + "/config.json"):
    
    with open("./config.json") as f:
        configData = json.load(f)

else:
    configTemplate = {"bannedWords": []}

    with open(os.getcwd() + "/config.json", "w+") as f:
        json.dump(configTemplate, f) 


#warn command

@bot.event
async def on_ready():
    for guild in bot.guilds:
        bot.warnings[guild.id] = {}
        
        async with aiofiles.open(f"{guild.id}.txt", mode="a") as temp:
            pass

        async with aiofiles.open(f"{guild.id}.txt", mode="r") as file:
            lines = await file.readlines()

            for line in lines:
                data = line.split(" ")
                member_id = int(data[0])
                admin_id = int(data[1])
                reason = " ".join(data[2:]).strip("\n")

                try:
                    bot.warnings[guild.id][member_id][0] += 1
                    bot.warnings[guild.id][member_id][1].append((admin_id, reason))

                except KeyError:
                    bot.warnings[guild.id][member_id] = [1, [(admin_id, reason)]] 
    
    print(bot.user.name + " is ready.")

@bot.event
async def on_guild_join(guild):
    bot.warnings[guild.id] = {}

@bot.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    if member is None:
        return await ctx.send("the member could not be found")

    if reason is None:
        return await ctx.send("please provide a reason")

    try:
        first_warning = False
        bot.warnings[ctx.guild.id][member.id][0] += 1
        bot.warnings[ctx.guild.id][member.id][1].append((ctx.author.id, reason))
    
    except KeyError:
        first_warning = True
        bot.warnings[ctx.guild.id][member.id] = [1, [(ctx.author.id, reason)]]

    count = bot.warnings[ctx.guild.id][member.id][0]

    async with aiofiles.open(f"{ctx.guild.id}.txt", mode="a") as file:
        await file.write(f"{member.id} {ctx.author.id} {reason}\n")

    await ctx.send(f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}.")


@bot.command()
@commands.has_permissions(administrator=True)
async def warnings(ctx, member: discord.Member=None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")
    
    embed = discord.Embed(title=f"Displaying Warnings for {member.name}", description="", colour=discord.Colour.red())
    try:
        i = 1
        for admin_id, reason in bot.warnings[ctx.guild.id][member.id][1]:
            admin = ctx.guild.get_member(admin_id)
            embed.description += f"**Warning {i}** given by: {admin.mention} for: *'{reason}'*.\n"
            i += 1

        await ctx.send(embed=embed)

    except KeyError: # no warnings
        await ctx.send("This user has no warnings.")


#level  system
@bot.event
async def on_member_join(member):
    with open('levels.json', 'r') as f:
        users = json.load(f)

    #wip

    await update_data(users, member)

    with open('levels.json', 'w') as f:
        json.dump(users, f)

@bot.event
async def on_message(message):
    with open('levels.json', 'r') as f:
        users = json.load(f)

        await update_data(users, message.author)
        await add_experience(users, message.author , 5)
        await level_up(users, message.author, message.channel)

    with open('levels.json' , 'r') as f:
        json.dump(users, f)

async def update_data(users, user):
    if not user.id in users:
        users[user.id] = {}
        users[user.id]['experience'] = 0
        users[user.id]['level'] = 1

async def add_experience(users, user, exp):
    users[user.id]['experience'] += exp

async def level_up(users, user , channel):
    experience = users[user.id]['experience']
    lvl_start = users[user.id]['level']
    lvl_end = int(experience ** (1/4))

    if lvl_start < lvl_end:
        await client.send_message(channel, '{} has leveled up to level {}'.format(user.mention, lvl_end))
        users[user.id]['level'] = lvl_end


# banned words [wip]

@slash.slash(name="addbannedwords", description="addbannedwords", guild_ids=guild_ids)
@commands.has_permissions(administrator=True)
async def addbannedword(ctx, word):
    if word.lower() in bannedWords:
        await ctx.send("Already banned")
    else:
        bannedWords.append(word.lower())

        with open("./config.json", "r+") as f:
            data = json.load(f)
            data["bannedWords"] = bannedWords
            f.seek(0)
            f.write(json.dumps(data))
            f.truncate()

        await ctx.message.delete()
        await ctx.send("Word added to banned words.")
    
@slash.slash(name="removewords", description="remove word from banned list", guild_ids=guild_ids)
@commands.has_permissions(administrator=True)
async def removebannedword(ctx, word):
    if word.lower() in bannedWords:
        bannedWords.remove(word.lower())

        with open("./config.json", "r+") as f:
            data = json.load(f)
            data["bannedWords"] = bannedWords
            f.seek(0)
            f.write(json.dumps(data))
            f.truncate()

        await ctx.message.delete()
        await ctx.send("Word remove from banned words.")
    else:
        await ctx.send("Word isn't banned.")

def msg_contains_word(msg, word):
    return re.search(fr'\b({word})\b', msg) is not None


@bot.event
async def on_message(message):
    messageAuthor = message.author

    if bannedWords != None and (isinstance(message.channel, discord.channel.DMChannel) == False):
        for bannedWord in bannedWords:
            if msg_contains_word(message.content.lower(), bannedWord):
                await message.delete()
                await message.channel.send(f"{messageAuthor.mention} your message was removed as it contained a banned word.")

    await bot.process_commands(message)

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
    
@slash.slash(name="whyrepostingisbad", description="Test command which returns the bot's ping", guild_ids=guild_ids)
async def whyrepostingisbad(ctx):
embed=discord.Embed(title="Why reposting i bad", url="https://stopmodreposts.org/assets/img/ZoI2D6yH_400x400.png")
embed.set_author(name="Berrysauce", url="https://stopmodreposts.org/assets/img/ZoI2D6yH_400x400.png", icon_url="https://stopmodreposts.org/assets/img/ZoI2D6yH_400x400.png")
embed.set_thumbnail(url="https://stopmodreposts.org/assets/img/ZoI2D6yH_400x400.png")
embed.add_field(name="What is reposting?", value="Reposting describes the uncredited re-uploading of (mostly copyrighted) files without the permission of the author. Reposting is one of the worst things a mod author can go through, and here is why:", inline=True)
embed.add_field(name="Malicious software", value="If a mod gets reposted, the mod author doesn't have any control over the files on the reposting site. This means that malware/adware could get on your computer when downloading/using the mod.", inline=True)
embed.add_field(name="No income for Developers", value="Developers live from income. If you download from reposting sites, they won't get any revenue, which could mean less mods from them in the future.", inline=True)
embed.add_field(name="Outdated versions", value="Reposting sites might link you to outdated versions, which could mean more bugs, crashes and errors for you.", inline=True)
embed.add_field(name="What we do", value="We do our best to provide you with up-to date site lists, a browser extension to block sites, and more.", inline=True)
embed.add_field(name="Block bad sites", value="Don't want to accidentally visit one? Download our browser extension to be safe!", inline=True)
embed.add_field(name="Maintain a list", value="We submit new sites periodically. Want to help other users? Find and upload sites so others won't download from them.", inline=True)
embed.add_field(name="Open Source on GitHub", value="You can visit our GitHub repository to view the site lists. Also, we're always happy about a star!", inline=True)
embed.set_footer(text="Join our discord sever:https://discord.gg/Pd9eMVzEYwdiscord")
await ctx.send(embed=embed)

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
#ban
@slash.slash(name="ban", description="bans people", guild_ids=guild_ids)
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.member, *, reason=None):
    await member.ban(reason =reason)
    await ctx.send(f"{member} got banned ")


@slash.slash(name="kick", description="kicks people", guild_ids=guild_ids)
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member} was kicked!")

#welcome user
@bot.event
async def on_member_join(member):
    guild = bot.get_guild(463457129588850699) 
    channel = guild.get_channel(783751248989913139)
    await channel.send(f'Hello {user.mention} and welcome to StopModReposts Discord sever you joining means so mutch us! :partying_face:')

#unban user
@slash.slash(name="unbans", description="unbans people who had gotten baned before", guild_ids=guild_ids)
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    bannedUsers = await ctx.guild.bans()
    name, discriminator = member.split("#")

    for ban in bannedUsers:
        user = ban.user

        if(user.name, user.discriminator) == (name, discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f"{user.mention} was unbanned.")
            return


bot.loop.create_task(update_stats())

# Run bot
bot.run(DISCORD_TOKEN)