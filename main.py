import os
import random
import asyncio
from datetime import date

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

members = []
global num_members


def erase_extra_chars(s):
    s = s.replace('[', '')
    s = s.replace(']', '')
    s = s.replace('\'', '')
    return s


def get_num_members():
    global num_members
    request = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Sheet1!a2").execute()
    temp_num = request.get('values', [])
    num_members = int(erase_extra_chars(str(temp_num)))


def get_members():
    global num_members
    for i in range(2, 2+num_members):
        request2 = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Sheet1!b" + str(i)).execute()
        temp_str = request2.get('values', [])
        members.append(erase_extra_chars(str(temp_str)))
    print(members)


def order_members(array):
    if len(array) > 1:
        # divide the list
        pivot = len(array) // 2
        left_part = array[:pivot]
        right_part = array[pivot:]

        order_members(left_part) # recursive
        order_members(right_part)

        i = j = k = 0  # loop variables

        while i < len(left_part) and j < len(right_part):
            if left_part[i] < right_part[j]:
                array[k] = left_part[i]
                i += 1
            else:
                array[k] = right_part[j]
                j += 1
            k += 1

        while i < len(left_part):
            array[k] = left_part[i]
            i += 1
            k += 1

        while j < len(right_part):
            array[k] = right_part[j]
            j += 1
            k += 1


def write_members():
    order_members(members)
    member_list = [[]]
    for i in range(0, num_members):
        temp_list = []
        temp_list.append(members[i])
        member_list.append(temp_list)
    member_list.pop(0)
    sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Sheet1!b2",
                          valueInputOption="USER_ENTERED", body={'values': member_list}).execute()


def find_member(member):
    for i in range (0,num_members):
        if members[i] == member:
            return i
    return 0


def check_date(msg):
    for i in range(0, 9):
        if i == 2 or i == 5:
            if msg[i] != '/':
                return False
        else:
            if not msg[i].isnumeric():
                return False
    if int(msg[0:2]) > 12 or int(msg[0:2]) < 1:
        return False
    if int(msg[3:5]) > 31 or int(msg[3:5]) < 1:
        return False
    if int(msg[6:10]) > 9999 or int(msg[6:10]) < 2023:
        return False
    return True


@client.event
async def on_ready():
    print(f'{client.user} is connected.\n')
    sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Sheet1!a1",
                          valueInputOption="USER_ENTERED", body={'values': [['MEMBERS']]}).execute()
    request = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Sheet1!a1").execute()
    names = request.get('values', [])
    print(names)

    get_num_members()

    get_members()


@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to my Discord server!'
    )


@client.event
async def on_message(message):
    global num_members
    for guild in client.guilds:
        if guild.name == GUILD:
            break
    if message.author == client.user:
        return
    member = message.author

    # registration/getting started
    if message.content == "SolePlan!":
        if member not in members:
            await member.create_dm()
            await member.dm_channel.send("Welcome to SolePlan! A central hub for all your planning needs!\n"
                                         "Type \"-help\" in these DM's to see what I can do for you!")
            members.append(str(member.name))
            num_members = num_members + 1
            sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Sheet1!a2",
                                  valueInputOption="USER_ENTERED", body={'values': [[num_members]]}).execute()
            sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Sheet1!c" + str(num_members + 1),
                                  valueInputOption="USER_ENTERED", body={'values': [['0']]}).execute()
            write_members()

    # dm messages
    if message.channel == member.dm_channel:
        def check(m):
            return m.author == m.author

        # help message
        if message.content == "-Help":
            await member.dm_channel.send("Here is the list of options: \n"
                                         "-Schedule: Schedule a new event my typing the date you wish so schedule it "
                                         "for, and then the name of the event. \n"
                                         "-Events: Lists all the events you currently have scheduled. \n"
                                         "-Delete: Delete one of the events you currently have scheduled. \n"
                                         "-Today: Lists all the upcoming events you have today.")

        # schedule event
        elif message.content == "-Schedule":
            await member.dm_channel.send("Give the date for the event: mm/dd/yyyy")
            try:
                msg = await client.wait_for("message", check=check, timeout=120)
                if len(msg.content) == 10 and check_date(str(msg.content)):
                    await member.dm_channel.send("What is the title of this event?")
                    try:
                        title = await client.wait_for("message", check=check, timeout=120)
                        loc = find_member(str(title.author.name)) + 2
                        request = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                                     range="Sheet1!c" + str(loc)).execute()
                        num_events = erase_extra_chars(str(request.get('values', [])))
                        event_loc = chr(ord('d') + int(num_events))
                        sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                              range="Sheet1!" + str(event_loc) + str(loc),
                                              valueInputOption="USER_ENTERED", body={'values':
                                              [[str(title.content) + "\n" + str(msg.content)]]}).execute()
                        num_events = int(num_events) + 1
                        sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                              range="Sheet1!c" + str(loc), valueInputOption="USER_ENTERED",
                                              body={'values': [[num_events]]}).execute()
                        await member.dm_channel.send("Your event has been scheduled!")
                    except asyncio.TimeoutError:
                        await member.dm_channel.send("Timeout: Scheduling has been cancelled.")
                        return
                else:
                    await member.dm_channel.send("Sorry, that is not a valid date.")
                    return
            except asyncio.TimeoutError:
                await member.dm_channel.send("Timeout: Scheduling has been cancelled.")
                return

        # view events
        elif message.content == "-Events":
            await member.dm_channel.send("Here are your current events: \n")
            loc = find_member(str(message.author.name)) + 2
            request = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                         range="Sheet1!c" + str(loc)).execute()
            num_events = erase_extra_chars(str(request.get('values', [])))
            for i in range (0,int(num_events)):
                request2 = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                              range="Sheet1!" + str(chr(ord('d') + i) + str(loc))).execute()
                curr_event = (erase_extra_chars(str(request2.get('values', []))))
                curr_event = curr_event.replace("n", "    ")
                await member.dm_channel.send(curr_event + "\n")

        # delete events
        elif message.content == "-Delete":
            loc = find_member(str(message.author.name)) + 2
            request = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                         range="Sheet1!c" + str(loc)).execute()
            num_events = erase_extra_chars(str(request.get('values', [])))
            if int(num_events) < 1:
                await member.dm_channel.send("You do not have any current events.")
                return
            await member.dm_channel.send("Type the name of the event you want to delete.")
            try:
                msg = await client.wait_for("message", check=check, timeout=120)
                list_events = []
                for i in range(0, int(num_events)):
                    request2 = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                                  range="Sheet1!" + str(chr(ord('d') + i) + str(loc))).execute()
                    sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                          range="Sheet1!" + str(chr(ord('d') + i) + str(loc)),
                                          valueInputOption="USER_ENTERED", body={'values': [[""]]}).execute()
                    curr_event = (erase_extra_chars(str(request2.get('values', []))))
                    curr_event = curr_event.replace("n", "    ")
                    list_events.append(curr_event)
                for i in range(0, len(list_events)):
                    if str(msg.content) in list_events[i]:
                        list_events.remove(list_events[i])
                        num_events = int(num_events) - 1
                        sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                              range="Sheet1!c" + str(loc),
                                              valueInputOption="USER_ENTERED", body={'values': [[num_events]]}).execute()
                        for j in range(0, num_events):
                            sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                                  range="Sheet1!" + str(chr(ord('d') + i) + str(loc)),
                                                  valueInputOption="USER_ENTERED",
                                                  body={'values': [[list_events[i]]]}).execute()
                        await member.dm_channel.send("This event has been deleted.")
                        return
                await member.dm_channel.send("No event with that name was found.")
            except asyncio.TimeoutError:
                await member.dm_channel.send("Timeout: Delete has been cancelled.")
                return

        # Morning Function
        elif message.content == "-Today":
            loc = find_member(str(message.author.name)) + 2
            request = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                         range="Sheet1!c" + str(loc)).execute()
            num_events = erase_extra_chars(str(request.get('values', [])))
            list_events = []
            for i in range(0, int(num_events)):
                request2 = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                              range="Sheet1!" + str(chr(ord('d') + i) + str(loc))).execute()
                curr_event = (erase_extra_chars(str(request2.get('values', []))))
                curr_event = curr_event.replace("n", "    ")
                list_events.append(curr_event)
            today = date.today()
            day = today.strftime("%m/%d/%Y")
            found = False
            for i in range(0,int(num_events)):
                if day in list_events[i]:
                    if not found:
                        await member.dm_channel.send("Today you have: \n")
                        found = True
                    await member.dm_channel.send(list_events[i] + "\n")
            if not found:
                await member.dm_channel.send("You do not have anything planned for today.")

client.run(TOKEN)

