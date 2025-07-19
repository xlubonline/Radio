from flask import Flask, Response, stream_with_context
import os

app = Flask(__name__)

AUDIO_FOLDER = "static/audio"
CHUNK_SIZE = 4096  # 4KB


def generate_audio_stream():
    audio_files = sorted(os.listdir(AUDIO_FOLDER))  # Stream in order
    for filename in audio_files:
        file_path = os.path.join(AUDIO_FOLDER, filename)
        if os.path.isfile(file_path) and filename.endswith(('.mp3', '.wav')):
            with open(file_path, 'rb') as f:
                while chunk := f.read(CHUNK_SIZE):
                    yield chunk


@app.route('/stream')
def stream_audio():
    return Response(
        stream_with_context(generate_audio_stream()),
        mimetype="audio/mpeg"  # or "audio/wav"
    )


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
