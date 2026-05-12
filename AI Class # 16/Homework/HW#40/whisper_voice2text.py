# pip install faster-whisper
# brew install ffmpeg
# brew install portaudio
# pip install SpeechRecognition pyaudio

from faster_whisper import WhisperModel

audio_file = "recording.wav"

model = WhisperModel(
    "base",      # tiny, base, small, medium, large
    device="cpu",
    compute_type="int8"
)

segments, info = model.transcribe(audio_file)
print("Language:", info.language)

for segment in segments:
    print(f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text}")
