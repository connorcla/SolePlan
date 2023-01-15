# bot.py
import asyncio
import os
import random
from datetime import datetime
import discord
from dotenv import load_dotenv

from googleapiclient.discovery import build
from google.oauth2 import service_account

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

# Set up google sheet connection
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'keys.json'
creds = None
creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
SAMPLE_SPREADSHEET_ID = '1rxQPvPHbJiE682GeWK_xIl14JcRd4jQDMaO__0T4Z9k'

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()
# Done with connection

memberlist = []

@client.event
async def on_ready():
    print(f'{client.user} is connected.\n')
    sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Sheet1!a1",
                          valueInputOption="USER_ENTERED", body={'values': [['Dog']]}).execute()
    request = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Sheet1!a1").execute()
    names = request.get('values', [])
    print(names)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == "Dog!":
        images = ["https://i.kym-cdn.com/entries/icons/original/000/008/342/ihave.jpg",
                  "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRoeG1Ou26bboi1iGmcRHFXBFHNilxaDmGZUg&usqp=CAU",
                  "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShDXzpCo448fjzZmzPDJwtAVF4AJKp3lGLHg&usqp=CAU"]

        response = random.choice(images)
        await message.channel.send(response)
    if str(message.content) == "SolePlan!":
        member = message.author
        #if member not in memberlist:
        print("register")
        await member.channel.send("Welcome to SolePlan! A central hub for all your planning needs!\n"
                                         "Type \"-help\" to see what I can do for you!")
    elif message.content == "-test":
        member = message.author
        await member.create_dm()
        await member.dm_channel.send("Yes dog.")


client.run(TOKEN)

