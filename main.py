from typing import cast
from dotenv import load_dotenv
import discord
import os

intents=discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
load_dotenv()

@client.event
async def on_message(message):
  channel = client.get_channel(int(os.getenv("DUMP_CHANNEL")))
  if message.author == client.user:
      return

  if (message.guild is None 
    and message.author != client.user
    and isinstance(channel, discord.TextChannel)):
    await channel.send("*" + message.content + "*")
    await message.reply('Ce message a bien été transmis au staff '\
'de la Grue Jaune, '\
'merci d\'avoir communiqué !')

client.run(os.getenv("TOKEN"))
