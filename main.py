import asyncio
import csv
import discord
from deep_translator import GoogleTranslator
import names
import nltk
nltk.download('punkt_tab')
nltk.download('stopwords')
from nltk.probability import FreqDist
from nltk.tokenize import RegexpTokenizer
import os
import randfacts
from discord import user
from typing import cast

from discord.message import Attachment

#Initialisation du bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

#Initialisation du store à messages
idStore = open("messages.csv", "r")
messagesList = {}
with idStore as lines:
  for line in lines:
    (key, val) = line.split(sep=";")
    messagesList[key] = val

#Initialisation du store à IDs
idStore = open("idStore.csv", "w+")
hashList = {}
with idStore as lines:
  for line in lines:
    (key, val) = line.split(sep=";")
    hashList[int(key)] = val

#Initialisation du store à pseudos
pseudoToId = {}
idToPseudo = {}

#Initialisation du store à autorisations
idAuto = open("autorisations.csv", "r")
autoList = {}
with idAuto as lines:
  for line in lines:
    (key, val) = line.split(sep=";")
    autoList[int(key)] = val

#Initialisation du store à sanctions
idSanc = open("sanctions.csv", "w+")
sancList = {}
with idSanc as lines:
  for line in lines:
    (key, val) = line.split(sep=";")
    sancList[str(key)] = val


@client.event
# Le bot ignore ses propres messages
async def on_message(message):
  if message.author == client.user:
    return

  # Salon où renvoyer les messages
  dumpChannel = client.get_channel(os.environ.get("DUMP_CHANNEL"))

  # Quelques faits culturels...
  if (message.author != client.user \
    and message.content.startswith("!funfact")):
    if message.content.startswith("!funfact++"):
      fact = randfacts.get_fact(only_unsafe=True)
    else:
      fact = randfacts.get_fact()
    await message.channel.send("Le saviez-vous ? " +\
        GoogleTranslator(source='en', target='fr').translate(fact))

  # Compteur de mots
  if (message.author != client.user \
    and message.content.startswith("!compteur")):
    message_contents = []
    async for m in message.channel.history(limit = None):
      message_contents.append(m.content)
    text = ' '.join(message_contents)
    tokenizer = RegexpTokenizer(r'\w+')
    clean_text = ' '.join(tokenizer.tokenize(text))
    tokens = nltk.word_tokenize(clean_text)

    # Retire la ponctuation
    stop_words = set(nltk.corpus.stopwords.words('french'))
    tokens = [t for t in tokens if t.lower() not in stop_words]
    fdist = FreqDist(tokens)
    most_common_words = fdist.most_common(10)
    await message.channel.send("Les mots les plus fréquents par ici sont: "\
      + str(most_common_words))

  # Gestion des DM
  anonymId = str(hash(str(message.author.id)))
  pseudo = ""
  if anonymId in idToPseudo:
    pseudo = idToPseudo[anonymId]
  if (message.guild is None and message.author != client.user
      and isinstance(dumpChannel, discord.TextChannel)\
      and not message.content.startswith("!funfact")\
      and not message.content.startswith("!compteur")\
     and (pseudo not in sancList or\
        sancList[pseudo] != "ignored")):
    thread = None

    # On vérifie si un thread déjà pour cette personne
    if anonymId in hashList:
      thread = dumpChannel.get_thread(hashList[anonymId])

    # Sinon on en crée un et on l'ajoute à la hashList
    if thread is None:
      pseudo = names.get_full_name()
      pseudoToId[pseudo] = anonymId
      idToPseudo[anonymId] = pseudo
      thread = await dumpChannel.create_thread(name = pseudo,\
        auto_archive_duration=10080)
      await dumpChannel.send("<#" + str(thread.id) + "> a démarré une discussion !")
      hashList[anonymId] = thread.id

      # On enregistre la nouvelle liste dans le store à IDs
      with open("idStore.csv", 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        for key, value in hashList.items():
          writer.writerow([key, value])

    # Envoi du message et info si KO/OK
    try:
      await thread.send(message.content, files=[await attachment.to_file()\
        for attachment in message.attachments])
    except discord.errors.HTTPException:
      await message.channel.send(messagesList["error_dm"])
      await dumpChannel.send(messagesList["error_report"])
      return
    await message.reply(messagesList["confirmation_dm"])
    
  # Gestion des réponses aux threads
  if (isinstance(message.channel, discord.Thread)
      and message.author != client.user and message.channel.name in pseudoToId):
    try:
      for member in message.channel.guild.members:
        if str(hash(str(member.id))) == pseudoToId[message.channel.name]:
          await member.send(message.content + "\n**" + \
            message.author.display_name + "**", \
            files=[await attachment.to_file()\
            for attachment in message.attachments])
    except asyncio.TimeoutError:
      await message.channel.send(messagesList["error_thread"])

  # Commandes dumpChannel
  if (message.channel == dumpChannel and message.author != client.user\
      and (message.author.id in autoList and\
        autoList[message.author.id] == "botadmin")): 
        # Pour ignorer les dm d'un user
        if message.content.startswith("!ignore"):
          line = message.content.split(sep=" ")
          if len(line) < 3:
            return
          else:
            sancList[line[1]+" "+line[2]] = "ignored"
            with open("idSanc.csv", 'w', newline='') as f:
              writer = csv.writer(f, delimiter=';')
              for key, value in sancList.items():
                writer.writerow([key, value])
            await message.channel.send(\
              messagesList["confirmation_ignore"])
        # Pour retirer les commandes appliquées à un user
        if message.content.startswith("!annule"):
          line = message.content.split(sep=" ")
          if len(line) < 2:
            return
          else:
            sancList[line[1]+" "+line[2]] = ""
            with open("idSanc.csv", 'w', newline='') as f:
              writer = csv.writer(f, delimiter=';')
              for key, value in sancList.items():
                writer.writerow([key, value])
            await message.channel.send(\
              messagesList["confirmation_cancel"])
          
client.run(os.environ.get("TOKEN"))
