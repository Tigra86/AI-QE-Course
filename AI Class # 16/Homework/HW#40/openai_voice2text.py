from openai import OpenAI

client = OpenAI()

with open("recording.wav", "rb") as audio:

    transcript = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=audio
    )

print(transcript.text)
