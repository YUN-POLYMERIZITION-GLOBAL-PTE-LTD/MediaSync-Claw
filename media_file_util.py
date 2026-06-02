import os
import json
from urllib.parse import quote_plus
from media_frp_util import get_domain

def get_media_directory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")

def get_media_files():
    directory = get_media_directory()
    
    media_extensions = {'.mp4'}
    media_files = []
    
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                ext = os.path.splitext(item)[1].lower()
                if ext in media_extensions:
                    media_files.append(item_path)
    except OSError as e:
        return {'error': str(e)}
    
    media_files.sort(key=lambda a: a.lower())
    
    return media_files

def handle_openclaw():
    frp_domain = get_domain()
    if frp_domain is None:
        return json.dumps({
            "status": "success",
                "data": {
                    "type": "text",
                    "text": ""
                }
            })

    txt = "The file below is a playlist of all available media files.\n\n"
    media_files = get_media_files()
    if len(media_files) > 0:
        for media_file in media_files:
            media_file_name = os.path.basename(media_file)
            media_file_url = f"https://{frp_domain}/{media_file_name}"

            google_play_query = f"utm_source=google&utm_medium=cpc&url={media_file_url}"
            google_play_url = f"https://play.google.com/store/apps/details?id=com.yunpoly.aiplayer&referer={quote_plus(google_play_query)}"
            txt += f"{media_file_name}: {google_play_url}\n"
    
    return json.dumps({
            "status": "success",
                "data": {
                    "type": "text",
                    "text": txt
                }
            })

def handle(ctx):
    return handle_openclaw()