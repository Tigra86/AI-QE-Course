# pip install sounddevice scipy faster-whisper

import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import time
import sounddevice as sd

print(sd.query_devices())

sd.default.device = (1, None)

fs = 16000
seconds = 8

print("Recording starts in 2 seconds...")
time.sleep(2)

print("Speak now!")

audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype="float32", device=1)
sd.wait()

print("Recording finished")

write("recording.wav", fs, audio)

model = WhisperModel("base", device="cpu", compute_type="int8")

segments, info = model.transcribe(
    "recording.wav",
    beam_size=5,
    vad_filter=True
)

print("Detected language:", info.language)

for seg in segments:
    print(f"[{seg.start:.2f}-{seg.end:.2f}] {seg.text}")
