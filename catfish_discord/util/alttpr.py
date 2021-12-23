from pathlib import Path
import yaml
import pyz3r
import random
import requests
import re
import time
from catfish_discord.util.alttpr_mystery_doors import generate_doors_mystery
from catfish_discord.util.alttpr_doors import AlttprDoor
from bs4 import BeautifulSoup


def read_file(filepath):
    if not Path(filepath).is_file():
        return None

    with open(filepath, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None


async def get_preset(preset, hints, spoilers, allow_quickswap):
    preset_data = read_file(f'presets/alttpr/{preset.lower()}.yaml')
    if preset_data is None:
        return
    settings = preset_data['settings']
    doors = preset_data.get('doors', False)

    if doors:
        seed = None
        # seed = await AlttprDoor(
        #     settings=settings,
        #     spoilers=spoilers != "mystery",
        # ).generate_game()
    else:
        settings['hints'] = 'on' if hints else 'off'
        settings['tournament'] = False if spoilers == 'on' else True
        settings['spoilers'] = spoilers
        settings['allow_quickswap'] = allow_quickswap

        if preset_data.get('customizer', False):
            if 'l' not in settings:
                settings['l'] = {}
            for i in preset_data.get('forced_locations', {}):
                location = random.choice(
                    [loc for loc in i['locations'] if loc not in settings['l']])
                settings['l'][location] = i['item']

        seed = await pyz3r.alttpr(
            settings=settings,
            customizer=preset_data.get('customizer', False))
    return seed


def get_mystery(weights, spoilers="mystery"):
    if 'preset' in weights:
        rolled_preset = pyz3r.mystery.get_random_option(weights['preset']).lower()
        if rolled_preset == 'none':
            return generate_doors_mystery(weights=weights, spoilers=spoilers)
        else:
            preset_data = read_file(f'presets/alttpr/{rolled_preset}.yaml')
            settings = preset_data['settings']
            customizer = preset_data.get('customizer', False)
            doors = preset_data.get('doors', False)
            settings.pop('name', None)
            settings.pop('notes', None)
            settings['spoilers'] = spoilers
            custom_instructions = pyz3r.mystery.get_random_option(weights.get('custom_instructions', None))

            if customizer:
                if 'l' not in settings:
                    settings['l'] = {}
                for i in preset_data.get('forced_locations', {}):
                    location = random.choice(
                        [loc for loc in i['locations'] if loc not in settings['l']])
                    settings['l'][location] = i['item']

            return {
                'weights': weights,
                'settings': settings,
                'customizer': customizer,
                'doors': doors,
                'custom_instructions': custom_instructions
            }
    else:
        return generate_doors_mystery(weights=weights, spoilers=spoilers)


async def generate_mystery_game(weight_set, spoilers="mystery", tournament=True, allow_quickswap=True):
    weights = read_file(f'weights/{weight_set.lower()}.yaml')
    if weights is None:
        return
    mystery = get_mystery(weights, spoilers)

    if mystery['doors']:
        seed = None
        # seed = await AlttprDoor(
        #     settings=mystery.settings,
        #     spoilers=spoilers != "mystery",
        # ).generate_game()
    else:

        mystery['settings']['tournament'] = tournament
        mystery['settings']['allow_quickswap'] = allow_quickswap

        seed = await pyz3r.alttpr(settings=mystery['settings'], customizer=mystery['customizer'])
    return seed


async def get_multiworld(file_content):
    base_url = "https://archipelago.gg"
    result = {'seed_info_url': '', 'room_url': '', 'error': ''}
    files = {"file": ("players.zip", file_content, "multipart/form-data")}
    data = {'forfeit_mode': "auto-enabled"}
    response = requests.post(f'{base_url}/generate', data=data, files=files, allow_redirects=False)

    soup = BeautifulSoup(response.text, 'html.parser')
    check_result = soup.find(id='check-result')
    if check_result is not None:
        return None
    wait_suburi = re.findall('href="(.*)"', response.text)[0]
    wait_response = requests.get(f'{base_url}{wait_suburi}', allow_redirects=False)
    suburi = re.findall('href="(.*)"', wait_response.text)[0]
    counter = 0
    failed = False
    while '/seed/' not in suburi and counter < 30:
        time.sleep(2)
        wait_response = requests.get(f'{base_url}{wait_suburi}', allow_redirects=False)
        suburi = re.findall('href="(.*)"', wait_response.text)[0]
        if "Generation failed" in str(wait_response.content):
            failed = True
            break
        counter += 1

    if counter < 30 and not failed:
        seed = suburi.replace('/seed/', '')
        response = requests.get(f'{base_url}/new_room/{seed}', allow_redirects=False)
        room = re.findall('href="(.*)"', response.text)[0]

        result['seed_info_url'] = f"{base_url}{suburi}"
        result['room_url'] = f"{base_url}{room}"
        return result
    elif failed:
        error_message = re.findall('{(.*)}', wait_response.text)[0]
        result['error'] = '{'+error_message+'}'
        return result
    return None
