import discord
import os
from pathlib import Path
import pyz3r
import yaml
from os import walk

client = discord.Client()

async def generate_seed(message):
    message_parts = message.content.split(" ")
    if len(message_parts) != 2:
        await message.channel.send('Wrong format. Please try it again.')
        return

    present = message_parts[1]
    present_path = f'presets/alttpr/{present}.yaml'
    if not Path(present_path).is_file():
        await message.channel.send('Preset is not existing.')
        return
    present_data = {}
    with open(present_path, 'r') as stream:
        try:
            present_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)                
            return
    
    seed = await pyz3r.alttpr(
        settings=present_data['settings'])
    url = seed.url
    await message.channel.send(f'Goal: {present_data["goal_name"]}\nDescrption: {present_data["description"]}\nUrl: {url}')

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('$seed'):
        await generate_seed(message)

    if message.content.startswith('$presets'):
        response = ""      
        for (dirpath, dirnames, files) in walk("presets/alttpr"):
            count = 0
            for filename in files:
                present_path = f'{dirpath}/{filename}'
                present_name = filename.replace('.yaml','')
                with open(present_path, 'r') as stream:
                    try:
                        present_data = yaml.safe_load(stream)
                        response += f'Name: {present_name} | '
                        if "goal_name" in present_data.keys() and present_data["goal_name"]:
                            response += f'Goal: {present_data["goal_name"]}\n'
                        if "description" in present_data.keys() and present_data["description"]:
                            response += f'Descrption: {present_data["description"]}\n'
                        response += "\n"
                    except yaml.YAMLError as exc:
                        print(filename)
                        print(exc)                
                        return
                if count == 10:
                    await message.channel.send(response)
                    count = 0
                    response = ""
                count += 1
        await message.channel.send(response)
            


client.run(os.getenv('DISCORD_TOKEN'))