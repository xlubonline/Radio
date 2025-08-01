import logging
from flask import Flask, Response, stream_with_context
from flask_cors import CORS
from mutagen.mp3 import MP3
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

AUDIO_FOLDER = 'static/audio'
CHUNK_SIZE = 4096
stream_start_time = time.time()

# Build playlist dynamically
playlist = []
total_duration = 0

for filename in sorted(os.listdir(AUDIO_FOLDER)):
    if filename.endswith('.mp3'):
        path = os.path.join(AUDIO_FOLDER, filename)
        audio = MP3(path)
        duration = audio.info.length        # in seconds
        bitrate = audio.info.bitrate // 1000  # in kbps

        playlist.append({
            'file': filename,
            'duration': duration,
            'bitrate': bitrate
        })
        total_duration += duration

def get_current_track():
    elapsed = (time.time() - stream_start_time) % total_duration
    current_time = 0
    for track in playlist:
        if current_time + track['duration'] > elapsed:
            offset = elapsed - current_time
            return track, offset
        current_time += track['duration']
    return playlist[0], 0

def generate_stream():
    last_track_file = None
    while True:
        track, offset_seconds = get_current_track()
        file_path = os.path.join(AUDIO_FOLDER, track['file'])
        byte_rate = (track['bitrate'] * 1000) // 8  # bytes/sec
        offset_bytes = int(offset_seconds * byte_rate)

        # Log when a new song starts playing
        if track['file'] != last_track_file:
            logging.info(f"Now playing: {track['file']} (duration: {track['duration']:.2f}s)")

        last_track_file = track['file']

        with open(file_path, 'rb') as f:
            f.seek(offset_bytes)
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break  # End of file
                yield chunk

                # If track changes, break and load next
                new_track, _ = get_current_track()
                if new_track['file'] != track['file']:
                    break

@app.route('/stream/mal')
def stream_audio():
    headers = {
        'Content-Type': 'audio/mpeg',
        'Cache-Control': 'no-cache',
        'Accept-Ranges': 'bytes'
    }
    return Response(
        stream_with_context(generate_stream()),
        headers=headers
    )

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
