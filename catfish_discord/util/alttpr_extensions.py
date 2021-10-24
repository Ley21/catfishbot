import gzip
import json
import random
import string
import os

import aioboto3

from catfish_discord.util.progression_spoiler import create_progression_spoiler


async def write_progression_spoiler(seed, spoiler_type='spoiler'):
    filename = f"{spoiler_type}__{seed.hash}__{'-'.join(seed.code).replace(' ', '')}__{''.join(random.choices(string.ascii_letters + string.digits, k=4))}.txt"

    if spoiler_type == 'progression':
        sorted_dict = create_progression_spoiler(seed)
    else:
        sorted_dict = seed.get_formatted_spoiler(translate_dungeon_items=True)

    payload = gzip.compress(json.dumps(sorted_dict, indent=4).encode('utf-8'))
    session = aioboto3.Session()
    bucket_name = os.environ.get('AWS_SPOILER_BUCKET_NAME')
    spoiler_base_url = f"https://{bucket_name}s3.{os.environ.get('AWS_DEFAULT_REGION')}.amazonaws.com/spoiler"
    async with session.client('s3') as s3:
        await s3.put_object(
            Bucket=os.environ.get('AWS_SPOILER_BUCKET_NAME'),
            Key='spoiler/'+filename,
            Body=payload,
            ACL='public-read',
            ContentEncoding='gzip',
            ContentDisposition='attachment'
        )

        return f"{spoiler_base_url}/{filename}"
