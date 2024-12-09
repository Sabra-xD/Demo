from pydub import AudioSegment
from pydub.utils import make_chunks
import base64
import json
import requests
import os

# Sony API configuration
API_KEY = 'e45e_0691_b2688b4710eefa14afed1c6b4a7dff8c3b5e1dea25dec254708b2750275b335b'
API_URL = 'https://api.techhub.developer.sony.com/mss/api/inference'

# File paths
input_file = "D:/brentford_newcastle.mp3"  # Input file (e.g., MP3)
temp_dir = "temp_chunks"  # Directory to store temporary 30-second chunks
output_dir = "separated_audio"  # Directory to store separated audio

# Step 1: Convert input file to WAV
print("Converting input file to WAV...")
audio = AudioSegment.from_file(input_file)
wav_file = os.path.splitext(input_file)[0] + ".wav"
audio.export(wav_file, format="wav")

# Step 2: Split WAV file into 30-second chunks
print("Splitting WAV file into 30-second chunks...")
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)
chunk_length_ms = 30 * 1000  # 30 seconds
chunks = make_chunks(AudioSegment.from_file(wav_file), chunk_length_ms)

chunk_files = []
for i, chunk in enumerate(chunks):
    chunk_name = os.path.join(temp_dir, f"chunk_{i}.wav")
    chunk.export(chunk_name, format="wav")
    chunk_files.append(chunk_name)

# Step 3: Process each chunk through the Sony API
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

separated_files = []
for chunk_file in chunk_files:
    print(f"Processing chunk: {chunk_file}")

    # Read and encode audio in base64
    with open(chunk_file, 'rb') as f:
        audio_data = base64.b64encode(f.read()).decode('utf-8')

    # Prepare API payload
    payload = {
        'audio': [
            {
                'name': os.path.basename(chunk_file),
                'data': f'data:audio/wav;base64,{audio_data}'
            }
        ],
        'algorithm': {
            'name': 'default',
            'option': [
                {'name': 'targets', 'data': ['vocals', 'drums', 'bass', 'other']},
                {'name': 'start_point', 'data': 0}
            ]
        }
    }

    # Send request to the API
    headers = {'X-TH_API-Key': API_KEY, 'Content-Type': 'application/json'}
    response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        result = response.json()
        for output in result.get('output', []):
            # Decode base64 audio and save it
            audio_base64 = output['data'].split(',')[1]
            audio_content = base64.b64decode(audio_base64)
            separated_file = os.path.join(output_dir, output['name'])
            with open(separated_file, 'wb') as out_f:
                out_f.write(audio_content)
            print(f"Saved: {separated_file}")
            separated_files.append(separated_file)
    else:
        print(f"Failed to process chunk {chunk_file}: {response.text}")

# Step 4: Combine separated audio files into full tracks
# This step requires combining audio segments for each target track (e.g., vocals, drums).
# Use pydub's `concat` functionality or any preferred audio processing tool.

print("Audio separation process completed.")
