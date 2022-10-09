import os
import json
import requests
import discord
from discord import app_commands
from dotenv import load_dotenv
from yarl import URL

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SMR_GUILD_ID = 463457129588850699
client = discord.Client(application_id="785933469531504690", intents=discord.Intents.all())
tree = app_commands.CommandTree(client)

def checklist(url):
    try:
        r = requests.get("https://api.stopmodreposts.org/sites.txt")
        if r.status_code != 200:
            return f"⚠️ Failed with status code {r.status_code}"
    except ConnectionError:
        return "⚠️ Connection failed"

    if url in r.text:
        return True
    else:
        return False

@tree.command(name="check", description="Check if a site is listed")
async def check(interaction: discord.Interaction, url: str):
    url = URL(url).host.replace("http://", "").replace("https://", "").replace("www.", "")

    # List status
    list_status = checklist(url)
    if type(list_status) != bool:
        await interaction.response.send_message(f"List Error: {list_status}")
    elif list_status is False:
        await interaction.response.send_message(f"❌ **{url}** is not on our list")
    elif list_status is True:
        await interaction.response.send_message(f"✅ **{url}** is on our list")

@tree.command(name="submit", description="Submit a site for review")
async def submit(interaction: discord.Interaction, url: str, description: str):
    url = URL(url).host.replace("http://", "").replace("https://", "").replace("www.", "")

    data = {
        "domain": url,
        "description": f"VIA DC - {description}"
    }

    try:
        r = requests.post("https://report.stopmodreposts.org/api/v1/report?falsepositive=false", json=data)
    except ConnectionError:
        return "⚠️ Connection failed"

    res = json.loads(r.text)

    if r.status_code == 201:
        await interaction.response.send_message(f"✅ **{url}** reported! Thanks!")
    elif r.status_code == 409 or r.status_code == 400:
        await interaction.response.send_message(f"⚠️ Failed to report **{url}**!\nDetail: `{res['detail']}`")
    else:
        await interaction.response.send_message(f"⚠️ Failed with status code {r.status_code}")

async def main():
    async with client:
      await tree.sync(guild=SMR_GUILD_ID)
      await client.start(DISCORD_TOKEN)

client.run(DISCORD_TOKEN)