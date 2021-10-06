
import discord
import html2markdown
import datetime
import gettext
import os

translate = gettext.translation('catfishbot', localedir='locale', fallback=True, languages=[os.getenv('LANG')])
_ = translate.gettext

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


async def get_embed(emojis, seed):
    settings_map = await seed.randomizer_settings()
    meta = seed.data['spoiler'].get('meta', {})
    embed = discord.Embed(
        title=meta.get('name', _('Requested Seed')),
        description=html2markdown.convert(
            meta.get('notes', '')),
        color=discord.Colour.dark_green(),
        timestamp=datetime.datetime.fromisoformat(seed.data['generated']))
    if meta.get('spoilers', 'off') == "mystery":
        embed.add_field(
            name=_('Mystery Game'),
            value=_("No meta information is available for this game."),
            inline=False)
        embed.add_field(
            name=_('Item Placement'),
            value="**"+_('Glitches Required')+f":** {meta['logic']}",
            inline=True)
    else:
        if meta.get('special', False):
            embed.add_field(
                name=_('Festive Randomizer'),
                value=_("This game is a festive randomizer. Spooky!"),
                inline=False)
            item_functionality = settings_map['item_functionality'][meta['item_functionality']]
            embed.add_field(
                name=_('Settings'),
                value=("**"+_('Item Placement')+f":** {settings_map['item_placement'][meta['item_placement']]}\n"
                       "**"+_('Dungeon Items')+f":** {settings_map['dungeon_items'][meta['dungeon_items']]}\n"
                       "**"+_('Accessibility')+f":** {settings_map['accessibility'][meta['accessibility']]}\n"
                       "**"+_('World State')+f":** {settings_map['world_state'][meta['mode']]}\n"
                       "**"+_('Hints')+f":** {meta['hints']}\n"
                       "**"+_('Swords')+f":** {settings_map['weapons'][meta['weapons']]}\n"
                       "**"+_('Item Pool')+f":** {settings_map['item_pool'][meta['item_pool']]}\n"
                       "**"+_('Item Functionality')+f":** {item_functionality}"),
                inline=False
            )
        else:
            embed.add_field(
                name=_('Item Placement'),
                value=("**"+_('Glitches Required')+f":** {meta['logic']}\n"
                       "**"+_('Item Placement')+f":** {settings_map['item_placement'][meta['item_placement']]}\n"
                       "**"+_('Dungeon Items')+f":** {settings_map['dungeon_items'][meta['dungeon_items']]}\n"
                       "**"+_('Accessibility')+f":** {settings_map['accessibility'][meta['accessibility']]}"),
                inline=True)

            embed.add_field(
                name=_('Goal'),
                value=("**"+_('Goal')+f":** {settings_map['goals'][meta['goal']]}\n"
                       "**"+_('Open Tower')+f":** {meta.get('entry_crystals_tower', 'unknown')}\n"
                       "**"+_('Ganon Vulnerable')+f":** {meta.get('entry_crystals_ganon', 'unknown')}"),
                inline=True)
            entrance_shuffled = settings_map['entrance_shuffle'][meta['shuffle']] if 'shuffle' in meta else 'None'
            embed.add_field(
                name=_('Gameplay'),
                value=("**"+_('World State')+f":** {settings_map['world_state'][meta['mode']]}\n"
                       "**"+_('Entrance Shuffle')+f":** {entrance_shuffled}\n"
                       "**"+_('Boss Shuffle')+f":** {settings_map['boss_shuffle'][meta['enemizer.boss_shuffle']]}\n"
                       "**"+_('Enemy Shuffle')+f":** {settings_map['enemy_shuffle'][meta['enemizer.enemy_shuffle']]}\n"
                       "**"+_('Pot Shuffle')+f":** {meta.get('enemizer.pot_shuffle', 'off')}\n"
                       "**"+_('Hints')+f":** {meta['hints']}"),
                inline=True)
            item_functionality = settings_map['item_functionality'][meta['item_functionality']]
            embed.add_field(
                name=_('Difficulty'),
                value=("**"+_('Swords')+f":** {settings_map['weapons'][meta['weapons']]}\n"
                       "**"+_('Item Pool')+f":** {settings_map['item_pool'][meta['item_pool']]}\n"
                       "**"+_('Item Functionality')+f":** {item_functionality}\n"
                       "**"+_('Enemy Damage')+f":** {settings_map['enemy_damage'][meta['enemizer.enemy_damage']]}\n"
                       "**"+_('Enemy Health')+f":** {settings_map['enemy_health'][meta['enemizer.enemy_health']]}"),
                inline=True)
    embed.add_field(name=_('File Select Code'),
                    value=build_file_select_code(seed, emojis=emojis),
                    inline=False)
    embed.add_field(name=_('Permalink'), value=seed.url, inline=False)
    return embed


def build_file_select_code(seed, emojis=None):
    if emojis:
        emoji_list = list(map(lambda x: str(discord.utils.get(
            emojis, name=emoji_code_map[x])), seed.code))
        return ' '.join(emoji_list) + ' (' + '/'.join(seed.code) + ')'
    else:
        return '/'.join(seed.code)
