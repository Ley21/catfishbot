from pathlib import Path
import yaml
import pyz3r
import random
import requests
import re
import time
import codecs


async def get_preset(preset, hints, spoilers, allow_quickswap):
    present_path = f'presets/alttpr/{preset}.yaml'
    if not Path(present_path).is_file():
        return None

    with open(present_path, 'r') as stream:
        try:
            preset_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return
    if not preset_dict:
        return None

    settings = preset_dict['settings']
    settings['hints'] = 'on' if hints else 'off'
    settings['tournament'] = False if spoilers == 'on' else True
    settings['spoilers'] = spoilers
    settings['allow_quickswap'] = allow_quickswap

    if preset_dict.get('customizer', False):
        if 'l' not in settings:
            settings['l'] = {}
        for i in preset_dict.get('forced_locations', {}):
            location = random.choice(
                [loc for loc in i['locations'] if loc not in settings['l']])
            settings['l'][location] = i['item']

    seed = await pyz3r.alttpr(
        settings=settings,
        customizer=preset_dict.get('customizer', False))
    return seed


async def get_mystery(preset):
    weights_path = f'weights/{preset}.yaml'
    if not Path(weights_path).is_file():
        return None
    with open(weights_path, 'r') as stream:
        try:
            weights = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return

    settings, customizer = pyz3r.mystery.generate_random_settings(weights)

    seed = await pyz3r.alttpr(settings=settings, customizer=customizer)
    return seed


async def get_multiworld(file_content):
    base_url = "https://archipelago.gg"
    result = {'seed_info_url': '', 'room_url': '', 'error': ''}
    files = {"file": ("players.zip", file_content, "multipart/form-data")}
    data = {'forfeit_mode': "auto-enabled"}
    response = requests.post(f'{base_url}/generate', data=data, files=files, allow_redirects=False)

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
