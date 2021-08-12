import discord
import os
from pathlib import Path
import pyz3r
import yaml
from os import walk
import html2markdown
import datetime
import json

client = discord.Client()

emoji_code_map = {
    'Bow': 'Bow',
    'Boomerang': 'Boomerang',
    'Hookshot': 'Hookshot',
    'Bombs': 'Bombs',
    'Mushroom': 'Mushroom',
    'Magic Powder': 'Magic_Powder',
    'Ice Rod': 'Ice_rod',
    'Pendant': 'Pendant_of_courage',
    'Bombos': 'Medallion_Bombos',
    'Ether': 'Medallion_Ether',
    'Quake': 'Medallion_Quake',
    'Lamp': 'Lantern',
    'Hammer': 'Hammer',
    'Shovel': 'Shovel',
    'Flute': 'Ocarina',
    'Bugnet': 'Bugnet',
    'Book': 'Book',
    'Empty Bottle': 'Bottle_Empty',
    'Green Potion': 'Bottle_Green_Potion',
    'Somaria': 'Cane_Somaria',
    'Cape': 'Cape',
    'Mirror': 'Mirror',
    'Boots': 'Pegasus_Shoes',
    'Gloves': 'Power_Glove',
    'Flippers': 'Flippers',
    'Moon Pearl': 'Moon_Pearl',
    'Shield': 'Mirror_Shield',
    'Tunic': 'Tunic',
    'Heart': 'Heart_Container',
    'Map': 'Map',
    'Compass': 'Compass',
    'Big Key': 'Big_Key'
}


async def get_embed(emojis, seed):
    settings_map = await seed.randomizer_settings()
    meta = seed.data['spoiler'].get('meta', {})
    embed = discord.Embed(
        title=meta.get('name', 'Requested Seed'),
        description=html2markdown.convert(
            meta.get('notes', '')),
        color=discord.Colour.dark_green(),
        timestamp=datetime.datetime.fromisoformat(seed.data['generated']))
    if meta.get('spoilers', 'off') == "mystery":
        embed.add_field(
            name='Mystery Game',
            value="No meta information is available for this game.",
            inline=False)
        embed.add_field(
            name='Item Placement',
            value=f"**Glitches Required:** {meta['logic']}",
            inline=True)
    else:
        if meta.get('special', False):
            embed.add_field(
                name='Festive Randomizer',
                value="This game is a festive randomizer.  Spooky!",
                inline=False)
            embed.add_field(
                name='Settings',
                value=(f"**Item Placement:** {settings_map['item_placement'][meta['item_placement']]}\n"
                       f"**Dungeon Items:** {settings_map['dungeon_items'][meta['dungeon_items']]}\n"
                       f"**Accessibility:** {settings_map['accessibility'][meta['accessibility']]}\n"
                       f"**World State:** {settings_map['world_state'][meta['mode']]}\n"
                       f"**Hints:** {meta['hints']}\n"
                       f"**Swords:** {settings_map['weapons'][meta['weapons']]}\n"
                       f"**Item Pool:** {settings_map['item_pool'][meta['item_pool']]}\n"
                       f"**Item Functionality:** {settings_map['item_functionality'][meta['item_functionality']]}"
                       ),
                inline=False
            )
        else:
            embed.add_field(
                name='Item Placement',
                value="**Glitches Required:** {logic}\n**Item Placement:** {item_placement}\n**Dungeon Items:** {dungeon_items}\n**Accessibility:** {accessibility}".format(
                    logic=meta['logic'],
                    item_placement=settings_map['item_placement'][meta['item_placement']],
                    dungeon_items=settings_map['dungeon_items'][meta['dungeon_items']],
                    accessibility=settings_map['accessibility'][meta['accessibility']],
                ),
                inline=True)

            embed.add_field(
                name='Goal',
                value="**Goal:** {goal}\n**Open Tower:** {tower}\n**Ganon Vulnerable:** {ganon}".format(
                    goal=settings_map['goals'][meta['goal']],
                    tower=meta.get(
                        'entry_crystals_tower', 'unknown'),
                    ganon=meta.get(
                        'entry_crystals_ganon', 'unknown'),
                ),
                inline=True)
            embed.add_field(
                name='Gameplay',
                value="**World State:** {mode}\n**Entrance Shuffle:** {entrance}\n**Boss Shuffle:** {boss}\n**Enemy Shuffle:** {enemy}\n**Pot Shuffle:** {pot}\n**Hints:** {hints}".format(
                    mode=settings_map['world_state'][meta['mode']],
                    entrance=settings_map['entrance_shuffle'][meta['shuffle']
                                                              ] if 'shuffle' in meta else "None",
                    boss=settings_map['boss_shuffle'][meta['enemizer.boss_shuffle']],
                    enemy=settings_map['enemy_shuffle'][meta['enemizer.enemy_shuffle']],
                    pot=meta.get('enemizer.pot_shuffle', 'off'),
                    hints=meta['hints']
                ),
                inline=True)
            embed.add_field(
                name='Difficulty',
                value="**Swords:** {weapons}\n**Item Pool:** {pool}\n**Item Functionality:** {functionality}\n**Enemy Damage:** {damage}\n**Enemy Health:** {health}".format(
                    weapons=settings_map['weapons'][meta['weapons']],
                    pool=settings_map['item_pool'][meta['item_pool']],
                    functionality=settings_map['item_functionality'][meta['item_functionality']],
                    damage=settings_map['enemy_damage'][meta['enemizer.enemy_damage']],
                    health=settings_map['enemy_health'][meta['enemizer.enemy_health']],
                ),
                inline=True)
    embed.add_field(name='File Select Code', value=build_file_select_code(seed,
                                                                          emojis=emojis), inline=False)
    embed.add_field(name='Permalink', value=seed.url, inline=False)
    return embed


async def generate_seed(message):
    message_parts = message.content.split(" ")
    if len(message_parts) != 2:
        await message.channel.send('Wrong format. Please try it again.')
        return

    present = message_parts[1]
    present_path = f'presets/alttpr/{present}.yaml'
    custom_json = f'presets/alttpr/{present}.json'
    if not Path(present_path).is_file() and not Path(custom_json).is_file():
        await message.channel.send('Preset is not existing.')
        return
    await message.add_reaction('⌚')

    if Path(present_path).is_file():
        preset_dict = {}
        with open(present_path, 'r') as stream:
            try:
                preset_dict = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                return
        settings = preset_dict['settings']
        settings['hints'] = 'off'
        settings['tournament'] = False
        settings['spoilers'] = 'on'
        settings['allow_quickswap'] = True

        if preset_dict.get('customizer', False):
            if 'l' not in settings:
                settings['l'] = {}
            for i in preset_dict.get('forced_locations', {}):
                location = random.choice(
                    [l for l in i['locations'] if l not in settings['l']])
                settings['l'][location] = i['item']

        seed = await pyz3r.alttpr(
            settings=settings,
            customizer=preset_dict.get('customizer', False))

    if Path(custom_json).is_file():
        f = open(custom_json, "r")
        customizer_settings = json.loads(f.read())
        f.close()
        settings = pyz3r.customizer.convert2settings(
            customizer_save=customizer_settings, tournament=False)
        seed = await pyz3r.alttpr(
            settings=settings)

    emojis = message.guild.emojis
    embed = await get_embed(emojis, seed)
    message_send = await message.reply(embed=embed)

    await message.add_reaction('✅')
    await message.remove_reaction('⌚', message_send.author)


def build_file_select_code(seed, emojis=None):
    if emojis:
        emoji_list = list(map(lambda x: str(discord.utils.get(
            emojis, name=emoji_code_map[x])), seed.code))
        return ' '.join(emoji_list) + ' (' + '/'.join(seed.code) + ')'
    else:
        return '/'.join(seed.code)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!seed') or message.content.startswith('$seed'):
        await generate_seed(message)

    if message.content.startswith('!presets') or message.content.startswith('$presets'):
        response = ""
        for (dirpath, dirnames, files) in walk("presets/alttpr"):
            count = 0
            for filename in files:
                present_path = f'{dirpath}/{filename}'
                present_name = filename.replace('.yaml', '')
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
