import csv
import random
import logging
import asyncio
import signal
import time
from telethon import functions, types, TelegramClient, events, errors
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest, InviteToChannelRequest, GetParticipantsRequest
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define your API credentials
api_id = 10248430
api_hash = '42396a6ff14a569b9d59931643897d0d'
phone_number = '37125295236'
session_name = f"sessions/{phone_number}"

# Initialize the Telegram client
client = TelegramClient(session_name, api_id, api_hash)

# Define the messages in different languages
messages = {
    'start': "Choose language:\n1. 🇷🇺 - Russian\n2. 🇱🇻 - Latvian\n3. 🇬🇧 - English",
    'Russian': "Хотите вступить в группы? Добавьте меня в контакты и в чате напишите 'Добавлено'",
    'Latvian': "Vēlies pievienoties grupām? Pievieno mani kontaktos un uzraksti čatā 'Pievienoju'",
    'English': "Do you want to join the groups? Add me in contacts and write 'Added' in the chat"
}

# Load group information from CSV file
def load_groups_from_csv(csv_file):
    groups = []
    with open(csv_file, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            groups.append(row[0])
    return groups

groups = load_groups_from_csv('groups.csv')

# Dictionary to track user language preferences
user_languages = {}

# Substrings to filter out
filter_keywords = ['added', 'pievienoju', 'добавлено', '1', '2', '3']

video_url = "https://graph.org/file/3a352343c76ad3ee62527.mp4"

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handle_private_message(event):
    user_id = event.sender_id
    message_text = event.raw_text.lower()
    logging.info(f"Received message from {user_id}: {message_text}")

    try:
        if not any(keyword in message_text for keyword in filter_keywords):
            logging.info(f"Sending start message to {user_id}")
            await event.respond(messages['start'])
        elif message_text in ['1', '2', '3']:
            logging.info(f"User {user_id} selected language option {message_text}")
            
            if message_text == '1':
                user_languages[user_id] = 'Russian'
                caption = messages['Russian']
            elif message_text == '2':
                user_languages[user_id] = 'Latvian'
                caption = messages['Latvian']
            elif message_text == '3':
                user_languages[user_id] = 'English'
                caption = messages['English']
            
            # Send the video with the caption
            await client.send_file(user_id, video_url, caption=caption)
            
        elif message_text in ['added', 'pievienoju', 'добавлено']:
            user_language = user_languages.get(user_id, 'English')
            logging.info(f"User {user_id} wants to join groups with language {user_language}")
            if user_language:
                for group in groups:
                    retry_count = 5
                    while retry_count > 0:
                        try:
                            logging.info(f"Adding {user_id} to group {group}")
                            await client(functions.channels.InviteToChannelRequest(
                                channel=group,
                                users=[user_id]
                            ))
                            break
                        except sqlite3.OperationalError as e:
                            logging.warning(f"Database is locked, retrying... ({retry_count} attempts left)")
                            retry_count -= 1
                            time.sleep(1)  # Wait before retrying
                        except Exception as e:
                            await event.respond(f"Error: {e}")
                            return
                await event.respond("You have been added to the groups!")
    except Exception as e:
        logging.error(f"Error handling message from {user_id}: {e}")

async def main():
    await client.start(phone=phone_number)
    logging.info("Bot is running...")

    # Create a future that never completes
    await asyncio.Event().wait()

# Directly run the main function in the event loop
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
