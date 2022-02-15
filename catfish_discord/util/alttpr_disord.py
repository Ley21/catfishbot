import disnake
import html2markdown
import datetime

emoji_code_map = {
    'Bow': 'Bow',
    'Boomerang': 'Boomerang',
    'Hookshot': 'Hookshot',
    'Bombs': 'Bombs',
    'Mushroom': 'Mushroom',
    'Magic Powder': 'Magic_Powder',
    'Ice Rod': 'Ice_rod',
    'Pendant': 'Pendant_of_Courage',
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


async def get_embed(emojis, seed, title=None, name=False, notes=False):

    if hasattr(seed, 'doors') and seed.doors:
        return await get_doors_embed(emojis, seed, name, notes)

    settings_map = await seed.randomizer_settings()
    meta = seed.data['spoiler'].get('meta', {})
    default_title = meta.get('name', 'Requested Seed')
    title_seed = f'{title}' if title else default_title
    embed = disnake.Embed(
        title=title_seed,
        description=html2markdown.convert(
            meta.get('notes', '')),
        color=disnake.Colour.dark_green(),
        timestamp=datetime.datetime.fromisoformat(seed.data['generated']))
    if meta.get('spoilers', 'off') == "mystery":
        embed.add_field(
            name='Mystery Game',
            value="No meta information is available for this game.",
            inline=False)
        embed.add_field(
            name='Item Placement',
            value="**" + 'Glitches Required' + f":** {meta['logic']}",
            inline=True)
    else:
        if meta.get('special', False):
            embed.add_field(
                name='Festive Randomizer',
                value="This game is a festive randomizer. Spooky!",
                inline=False)
            item_functionality = settings_map['item_functionality'][meta['item_functionality']]
            embed.add_field(
                name='Settings',
                value=("**" + 'Item Placement' + f":** {settings_map['item_placement'][meta['item_placement']]}\n"
                       "**" + 'Dungeon Items' + f":** {settings_map['dungeon_items'][meta['dungeon_items']]}\n"
                       "**" + 'Accessibility' + f":** {settings_map['accessibility'][meta['accessibility']]}\n"
                       "**" + 'World State' + f":** {settings_map['world_state'][meta['mode']]}\n"
                       "**" + 'Hints' + f":** {meta['hints']}\n"
                       "**" + 'Swords' + f":** {settings_map['weapons'][meta['weapons']]}\n"
                       "**" + 'Item Pool' + f":** {settings_map['item_pool'][meta['item_pool']]}\n"
                       "**" + 'Item Functionality' + f":** {item_functionality}"),
                inline=False
            )
        else:
            embed.add_field(
                name='Item Placement',
                value=("**" + 'Glitches Required' + f":** {meta['logic']}\n"
                       "**" + 'Item Placement' + f":** {settings_map['item_placement'][meta['item_placement']]}\n"
                       "**" + 'Dungeon Items' + f":** {settings_map['dungeon_items'][meta['dungeon_items']]}\n"
                       "**" + 'Accessibility' + f":** {settings_map['accessibility'][meta['accessibility']]}"),
                inline=True)

            embed.add_field(
                name='Goal',
                value=("**" + 'Goal' + f":** {settings_map['goals'][meta['goal']]}\n"
                       "**" + 'Open Tower' + f":** {meta.get('entry_crystals_tower', 'unknown')}\n"
                       "**" + 'Ganon Vulnerable' + f":** {meta.get('entry_crystals_ganon', 'unknown')}"),
                inline=True)
            entrance_shuffled = settings_map['entrance_shuffle'][meta['shuffle']] if 'shuffle' in meta else 'None'
            embed.add_field(
                name='Gameplay',
                value=("**" + 'World State' + f":** {settings_map['world_state'][meta['mode']]}\n"
                       "**" + 'Entrance Shuffle' + f":** {entrance_shuffled}\n"
                       "**" + 'Boss Shuffle' + f":** {settings_map['boss_shuffle'][meta['enemizer.boss_shuffle']]}\n"
                       "**" + 'Enemy Shuffle' + f":** {settings_map['enemy_shuffle'][meta['enemizer.enemy_shuffle']]}\n"
                       "**" + 'Pot Shuffle' + f":** {meta.get('enemizer.pot_shuffle', 'off')}\n"
                       "**" + 'Hints' + f":** {meta['hints']}"),
                inline=True)
            item_functionality = settings_map['item_functionality'][meta['item_functionality']]
            embed.add_field(
                name='Difficulty',
                value=("**" + 'Swords' + f":** {settings_map['weapons'][meta['weapons']]}\n"
                       "**" + 'Item Pool' + f":** {settings_map['item_pool'][meta['item_pool']]}\n"
                       "**" + 'Item Functionality' + f":** {item_functionality}\n"
                       "**" + 'Enemy Damage' + f":** {settings_map['enemy_damage'][meta['enemizer.enemy_damage']]}\n"
                       "**" + 'Enemy Health' + f":** {settings_map['enemy_health'][meta['enemizer.enemy_health']]}"),
                inline=True)
    embed.add_field(name='File Select Code',
                    value=build_file_select_code(seed, emojis=emojis),
                    inline=False)
    embed.add_field(name='Permalink', value=seed.url, inline=False)
    return embed


async def get_doors_embed(emojis, seed, name=False, notes=False):
    embed = disnake.Embed(
        title=name if name else "Requested Seed",
        description=notes if notes else "Requested Door Randomizer Game.",
        color=disnake.Colour.dark_red()
    )

    embed.add_field(
        name='Door Randomizer',
        value="This game was generated using Aerinon's Door Randomizer.",
        inline=False)

    embed.add_field(name='File Select Code', value=build_file_select_code(seed, emojis=emojis), inline=False)

    embed.add_field(name='Permalink', value=seed.url, inline=False)

    if seed.spoilers:
        embed.add_field(name='Spoiler Log', value=seed.spoiler_url, inline=False)
        if seed.attempts > 1:
            embed.add_field(name='Generation Attempts', value=seed.attempts, inline=False)

    embed.add_field(name="Version", value=seed.version)
    return embed


def build_file_select_code(seed, emojis=None):
    if emojis:
        emoji_list = list(map(lambda x: str(disnake.utils.get(
            emojis, name=emoji_code_map[x])), seed.code))
        return ' '.join(emoji_list) + ' (' + '/'.join(seed.code) + ')'
    else:
        return '/'.join(seed.code)
