import json
import boto3
import discord
import requests

# CONFIGURATION
# Input GDrive file IDS
files_to_monitor = ['1GIxbI86LPfyURo-DySauYoeKqj1k-H2nedzTeDnHD58']
# Input Discord user IDS
users_to_notify = ['189502176815480832']
# END CONFIGURATION

def lambda_handler(event, context):
    # Import AWS SSM API client
    # Note it uses the Lambda role
    ssm = boto3.client('ssm')

    # Get bot token from SSM /adi-gdrive-checker/bot-token
    discord_bot_token = ssm.get_parameter(Name='/adi-gdrive-checker/bot-token', WithDecryption=True)['Parameter'][
        'Value']
    # Get files to monitor from SSM /adi-gdrive-checker/files
    files_to_monitor_data = json.loads(
        ssm.get_parameter(Name='/adi-gdrive-checker/files', WithDecryption=True)['Parameter']['Value'])
    # Get drive API key from SSM /adi-gdrive-checker/drive-key
    drive_key = ssm.get_parameter(Name='/adi-gdrive-checker/drive-key', WithDecryption=True)['Parameter']['Value']

    # Connect to Discord
    discord_client = discord.Client()
    discord_client.run(discord_bot_token)

    try:
        for file_id in files_to_monitor:
            print(f'Now checking {file_id}')
            # Loop through files_to_monitor_data to get the dict that holds all the metadata for this current file
            given_file_in_data = next((file for file in files_to_monitor_data if file['id'] == file_id), None)

            # If the file doesn't exist in the param store we will just create it and then break
            if given_file_in_data is None:
                files_to_monitor_data.append({'id': file_id, 'last_updated': '2222222'})

            saved_last_updated_time = given_file_in_data['last_updated']

            # Fetch the modifiedTime from GDrive API
            # Authorize the request with API key
            gdrive_req = requests.get(f'https://www.googleapis.com/drive/v3/files/{file_id}',
                                      params={'fields': 'name,modifiedTime', 'key': str(drive_key)}).json()
            print(str(gdrive_req))
            file_name = gdrive_req['name']
            real_last_updated_time = gdrive_req['modifiedTime']

            # Do notifications if the saved and real last updated time differ
            if saved_last_updated_time != real_last_updated_time:
                # Temporarily write the new time to the data inside this script...
                saved_last_updated_time = real_last_updated_time

                # Push the notifications to Discord
                for user in users_to_notify:
                    try:
                        await discord_client.get_user(int(user)).send(f'File {file_name} was updated at {real_last_updated_time}!')
                    except Exception as e:
                        print(e)
    finally:
        # Write back the entire modified json array to SSM
        data_to_write_back = json.dumps(files_to_monitor_data)

        print(json.dumps(data_to_write_back))

        ssm.put_parameter(Name='/adi-gdrive-checker/files', Value=data_to_write_back, Overwrite=True)

        # End the execution
        return

