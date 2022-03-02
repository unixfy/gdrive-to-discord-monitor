import asyncio
import json
from datetime import datetime

import boto3
import discord
import requests

# CONFIGURATION
# Input GDrive file IDS
files_to_monitor = ['1GIxbI86LPfyURo-DySauYoeKqj1k-H2nedzTeDnHD58', '1VA01N-2lEYn1EITXmk89CNfGJovwaTXR']
# Input Discord user IDS
users_to_notify = ['189502176815480832']

# END CONFIGURATION

# Import AWS SSM API client
# Note it uses the Lambda role
ssm = boto3.client('ssm')


class DiscordClient(discord.Client):
    async def on_ready(self):
        await self.wait_until_ready()
        print('Logged in Discord')
        print('Calling file handler')
        # Now all the files will be checked
        await handle_files(self)
        # And break the event loop
        await self.logout()


async def handle_files(discord_client):
    # Get files to monitor from SSM /adi-gdrive-checker/files
    files_to_monitor_data = json.loads(
        ssm.get_parameter(Name='/adi-gdrive-checker/files', WithDecryption=True)['Parameter']['Value'])
    print(files_to_monitor_data)
    # Get drive API key from SSM /adi-gdrive-checker/drive-key
    drive_key = ssm.get_parameter(Name='/adi-gdrive-checker/drive-key', WithDecryption=True)['Parameter']['Value']
    print(drive_key)

    try:
        for file_id in files_to_monitor:
            print(f'Now checking {file_id}')
            # Loop through files_to_monitor_data to get the dict that holds all the metadata for this current file
            given_file_in_data = next((file for file in files_to_monitor_data if file['id'] == file_id), None)

            # If the file doesn't exist in the param store we will just create it and then break
            if given_file_in_data is None:
                files_to_monitor_data.append({"id": file_id, "last_updated": "123456"})
                break

            saved_last_updated_time = given_file_in_data['last_updated']

            # Fetch the modifiedTime from GDrive API
            # Authorize the request with API key
            gdrive_req = requests.get(f'https://www.googleapis.com/drive/v3/files/{file_id}',
                                      params={'fields': 'name,modifiedTime,webViewLink', 'key': str(drive_key),
                                              'supportsAllDrives': True},
                                      headers={'Pragma': 'No-Cache', 'Cache-Control': 'No-Cache'}).json()
            print(str(gdrive_req))
            file_name = gdrive_req['name']
            file_link = gdrive_req['webViewLink']
            real_last_updated_time = gdrive_req['modifiedTime']

            # Do notifications if the saved and real last updated time differ
            if saved_last_updated_time != real_last_updated_time:
                # Temporarily write the new time to the data inside this script...
                given_file_in_data['last_updated'] = real_last_updated_time

                # # Build a little embed
                # embed = discord.Embed(title="File updated!",
                #                       description=f"File {file_name} was updated! See timestamp below or click to open in Drive.",
                #                       url=f"{file_link}")
                # embed.timestamp = datetime.fromisoformat(real_last_updated_time)

                # Push the notifications to Discord
                for user in users_to_notify:
                    print(f"Now notifying {user} for {file_id}")
                    try:
                        dest_user = await discord_client.fetch_user(int(user))
                        # Send the message to user
                        await dest_user.send(
                            f"The file {file_name} was updated at {real_last_updated_time}. [Click here]({file_link})")
                    except Exception as e:
                        print(e)
            else:
                print(f'Did not need to notify {file_id}')
    finally:
        data_to_write_back = json.dumps(files_to_monitor_data)

        print(json.dumps(data_to_write_back))

        # Write back the entire modified json array to SSM
        ssm.put_parameter(Name='/adi-gdrive-checker/files', Value=data_to_write_back, Overwrite=True)

        # End the execution
        return


async def run():
    # Get bot token from SSM /adi-gdrive-checker/bot-token
    discord_bot_token = ssm.get_parameter(Name='/adi-gdrive-checker/bot-token', WithDecryption=True)['Parameter'][
        'Value']
    print(discord_bot_token)

    # Connect to Discord
    print("Logging in Discord")
    discord_client = DiscordClient()

    # Connect to Discord
    # Note this is blocking
    await discord_client.start(str(discord_bot_token))


def lambda_handler(event, context):
    # Somehow we have to do this (instead of just calling client.run()) because client.run will close the event loop at the end...
    asyncio.get_event_loop().run_until_complete(run())
