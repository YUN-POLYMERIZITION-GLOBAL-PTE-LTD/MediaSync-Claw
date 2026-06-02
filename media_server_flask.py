#!/usr/bin/env python3
"""
OpenClaw Skill: Media File Server with FRP Support (Flask Version)

This skill implements a media file server that:
1. Traverses and lists multimedia files in the media-file-server directory
2. Serves media files with proper MIME types for playback
3. Integrates with FRP for remote access
"""

import os
import mimetypes
from pathlib import Path
from urllib.parse import quote_plus
from flask import Flask, send_from_directory, render_template, abort, jsonify
from media_frp_util import get_domain, setup_frp
from media_file_util import get_media_directory, get_media_files


# Initialize Flask app
app = Flask(__name__, template_folder='templates')

def guess_mime_type(filepath):
    """Enhanced MIME type guessing for media files."""
    # Add common media file extensions if not already registered
    media_types = {
        '.mp4': 'video/mp4'
    }
    
    # Get file extension
    ext = Path(filepath).suffix.lower()
    if ext in media_types:
        return media_types[ext]
    
    # Fall back to default MIME type detection
    mime_type, _ = mimetypes.guess_type(filepath)
    return mime_type or 'application/octet-stream'

@app.route('/api/openclaw', methods=['POST'])
def handle_api_openclaw():
    frp_domain = get_domain()

    txt = "The file below is a playlist of all available media files.\n\n"
    media_files = get_media_files()
    if len(media_files) > 0:
        for media_file in media_files:
            media_file_name = os.path.basename(media_file)
            media_file_url = f"https://{frp_domain}/{media_file_name}"

            google_play_query = f"url={quote_plus(media_file_url)}"
            google_play_url = f"https://play.google.com/store/apps/details?id=com.yunpoly.aiplayer&referrer={quote_plus(google_play_query)}"
            txt += f"{media_file_name}: {google_play_url}\n"
    
    # return jsonify({
    #         "status": "success",
    #             "data": {
    #                 "type": "text",
    #                 "text": txt
    #             }
    #         })
    return jsonify({
        "success": True,
        "action": "reply",
        "abort": True,
        "reply": txt,
        "result": "Success"
    }), 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_media(path):
    """Serve media files and directory listings."""
    media_dir = get_media_directory()
    
    # Security check: prevent directory traversal attacks
    safe_path = os.path.normpath(os.path.join(media_dir, path))
    
    # Ensure the path is within the media directory
    if not safe_path.startswith(os.path.abspath(media_dir)):
        abort(403)  # Forbidden
    
    if os.path.isdir(safe_path):
        return list_directory(safe_path, media_dir)
    elif os.path.isfile(safe_path):
        directory = os.path.dirname(safe_path)
        filename = os.path.basename(safe_path)
        
        # Guess MIME type
        mime_type = guess_mime_type(safe_path)
        
        # Serve the file
        return send_from_directory(directory, filename, mimetype=mime_type)
    else:
        abort(404)

def list_directory(path, media_dir):
    try:
        file_list = os.listdir(path)
    except OSError:
        abort(404)
    
    # Filter and sort media files
    media_extensions = {'.mp4'}
    media_files = []
    other_files = []
    directories = []
    
    for name in file_list:
        fullname = os.path.join(path, name)
        if os.path.isdir(fullname):
            directories.append(name)
        else:
            ext = os.path.splitext(name)[1].lower()
            if ext in media_extensions:
                media_files.append(name)
            else:
                other_files.append(name)
    
    # Sort all lists
    media_files.sort(key=lambda a: a.lower())
    other_files.sort(key=lambda a: a.lower())
    directories.sort(key=lambda a: a.lower())
    
    # Get relative path for display
    rel_path = os.path.relpath(path, media_dir)
    if rel_path == '.':
        display_path = '/'
    else:
        display_path = '/' + rel_path.replace('\\', '/')

    return render_template('medias.html', display_path=display_path, directories=directories, media_files=media_files)

def setup_media_server(port=8000):
    """
    Start the media file server on the specified port.
    
    Args:
        port (int): Port number to listen on (default: 8000)
    
    Returns:
        None
    """
    current_file_path = os.path.abspath(__file__)
    current_directory = os.path.dirname(current_file_path)
    os.chdir(current_directory)
    
    print("Press Ctrl+C to stop the server")
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\nShutting down the server...")
    except Exception as e:
        print(f"Error starting server: {e}")

def main():
    setup_frp(port=8000)
    
    # Start the media server with or without HTTPS
    setup_media_server(port=8000)

if __name__ == '__main__':
    main()