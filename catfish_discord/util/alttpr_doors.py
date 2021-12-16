import tempfile
import os
import string
import json
import random
import asyncio
from tenacity import RetryError, AsyncRetrying, stop_after_attempt, retry_if_exception_type
import aiofiles
import aioboto3
import gzip
import re


class AlttprDoor():
    def __init__(self, settings=None, spoilers=True):
        self.settings = settings
        self.spoilers = spoilers

    async def generate_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_file_path = os.path.join(tmp, "settings.json")
            self.hash = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

            self.settings['outputpath'] = tmp
            self.settings['outputname'] = self.hash
            self.settings['create_rom'] = True
            self.settings['create_spoiler'] = True
            self.settings['calc_playthrough'] = False
            self.settings['rom'] = os.environ.get('ALTTP_ROM')

            # Currently not working
            #self.settings['enemizercli'] = os.path.join(os.environ.get('ENEMIZER_HOME'), 'EnemizerCLI.Core')

            # set some defaults we do NOT want to change ever
            self.settings['count'] = 1
            self.settings['multi'] = 1
            self.settings['names'] = ""
            self.settings['race'] = not self.spoilers

            with open(settings_file_path, "w") as f:
                json.dump(self.settings, f)
            attempts = 0
            try:
                async for attempt in AsyncRetrying(stop=stop_after_attempt(10), retry=retry_if_exception_type(Exception)):
                    with attempt:
                        attempts += 1
                        proc = await asyncio.create_subprocess_exec(
                            'python',
                            'DungeonRandomizer.py',
                            '--settingsfile', settings_file_path,
                            '--rom', os.environ.get("ALTTP_ROM"),
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=os.environ.get('DOOR_RANDO_HOME'))

                        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=20)
                        if proc.returncode > 0:
                            raise Exception(f'Exception while generating game: {stderr.decode()}')
            except RetryError as e:
                raise e.last_attempt._exception from e

            self.patch_name = "DR_" + self.settings['outputname'] + ".bps"
            self.rom_name = "DR_" + self.settings['outputname'] + ".sfc"
            self.spoiler_name = "DR_" + self.settings['outputname'] + "_Spoiler.txt"

            rom_path = os.path.join(tmp, self.rom_name)
            patch_path = os.path.join(tmp, self.patch_name)
            spoiler_path = os.path.join(tmp, self.spoiler_name)

            filps_name = 'flips.exe' if os.name == 'nt' else 'flips'
            proc = await asyncio.create_subprocess_exec(
                os.path.join('utils', filps_name),
                '--create',
                '--bps-delta',
                os.environ.get("ALTTP_ROM"),
                rom_path,
                patch_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()

            if proc.returncode > 0:
                raise Exception(f'Exception while while creating patch: {stderr.decode()}')

            async with aiofiles.open(patch_path, "rb") as f:
                patch_file = await f.read()

            session = aioboto3.Session()
            bucket_name = os.environ.get('AWS_SPOILER_BUCKET_NAME')
            base_url = f"https://{bucket_name}s3.{os.environ.get('AWS_DEFAULT_REGION')}.amazonaws.com"

            async with session.client('s3') as s3:
                await s3.put_object(
                    Bucket=bucket_name,
                    Key='patch/' + self.patch_name,
                    Body=patch_file,
                    ACL='public-read'
                )

            async with aiofiles.open(spoiler_path, "rb") as f:
                self.spoiler_file = await f.read()

            async with session.client('s3') as s3:
                await s3.put_object(
                    Bucket=bucket_name,
                    Key='spoiler/' + self.spoiler_name,
                    Body=gzip.compress(self.spoiler_file),
                    ACL='public-read',
                    ContentEncoding='gzip',
                    ContentDisposition='attachment'
                )

            self.patch_url = f"{base_url}/patch/{self.patch_name}"
            self.spoiler_url = f"{base_url}/spoiler/{self.spoiler_name}"

    @property
    def url(self):
        return f"{os.environ.get('ALTTPR_PATCHER_URL')}?patch={self.patch_url}"

    @property
    def code(self):
        file_select_code = re.search("Hash:*\s(.*,.*,.*,.*,.*)", self.spoiler_file.decode()).groups()[0]
        code = list(file_select_code.split(', '))
        code_map = {
            'Bomb': 'Bombs',
            'Powder': 'Magic Powder',
            'Rod': 'Ice Rod',
            'Ocarina': 'Flute',
            'Bug Net': 'Bugnet',
            'Bottle': 'Empty Bottle',
            'Potion': 'Green Potion',
            'Cane': 'Somaria',
            'Pearl': 'Moon Pearl',
            'Key': 'Big Key'
        }
        p = list(map(lambda x: code_map.get(x, x), code))
        return [p[0], p[1], p[2], p[3], p[4]]

    @property
    def doors(self):
        return True