import discord
from discord import Intents
import os
import requests
import json
import random
from pymongo import MongoClient
from dotenv import load_dotenv
from keep_alive import keep_alive


#Load the environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

#Initializing MongoDB Client
client = MongoClient(MONGO_URI)
db = client.get_database("encourage_bot_db")
encouragements_collection = db.get_collection("encouragements")


intents = Intents.default()
discord_client = discord.Client(intents=intents)

sad_words = ["sad", "depressed", "unhappy", "angry", "miserable", "depressing"]

starter_encouragements = [
  "Cheer up!",
  "Hang in there.",
  "You are a great person / bot!"
]

if encouragements_collection.count_documents({"responding": {"$exists": True}}) == 0:
    encouragements_collection.insert_one({"messages": [], "responding": True})

def get_quote():
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]['q'] + " -" + json_data[0]['a']
  return (quote)

def update_encouragements(encouraging_message):
    if encouragements_collection.count_documents({}) > 0:
        encouragements = encouragements_collection.find_one()["messages"]
        encouragements.append(encouraging_message)
        encouragements_collection.update_one({}, {"$set": {"messages": encouragements}})
    else:
        encouragements_collection.insert_one({"messages": [encouraging_message]})


def delete_encouragements(index):
    encouragements = encouragements_collection.find_one()["messages"]
    if len(encouragements) > index:
        del encouragements[index]
    encouragements_collection.update_one({}, {"$set": {"messages": encouragements}})
   
@discord_client.event
async def on_ready():
  print(f"We have logged in as {discord_client.user}")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    msg = message.content

    if msg.startswith("$inspire"):
        quote = get_quote()
        await message.channel.send(quote)
    

    encouragements = encouragements_collection.find_one()
    if encouragements["responding"]:
        options = starter_encouragements + encouragements["messages"]


        if any(word in msg for word in sad_words):
            await message.channel.send(random.choice(options))

    if msg.startswith("$new"):
        encouraging_message = msg.split("$new ", 1)[1]
        update_encouragements(encouraging_message)
        await message.channel.send("New encouraging message added.")

    if msg.startswith("$del"):
        encouragements = []
        if encouragements_collection.count_documents({}) > 0:
            index = int(msg.split("$del", 1)[1])
            delete_encouragements(index)
            encouragements = encouragements_collection.find_one()["messages"]
        await message.channel.send(encouragements)
    
    if msg.startswith("$list"):
        encouragements = encouragements_collection.find_one()["messages"]
        await message.channel.send(encouragements)
    
    if msg.startswith("$responding"):
        value = msg.split("$responding ", 1)[1]

        if value.lower() == "true":
            encouragements_collection.update_one({}, {"$set": {"responding": True}})
            await message.channel.send("Responding is on.")
        else:
            encouragements_collection.update_one({}, {"$set": {"responding": False}})
            await message.channel.send("Responding is off.")

if TOKEN is None:
    raise ValueError("The TOKEN environment variable is not set")

if MONGO_URI is None:
    raise ValueError("The MONGO_URI environment variable is not set")

keep_alive()
discord_client.run(TOKEN)