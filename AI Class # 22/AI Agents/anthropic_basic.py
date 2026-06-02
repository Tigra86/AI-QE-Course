from anthropic import Anthropic

client = Anthropic()

resp = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=512,
    messages=[{"role": "user", "content": "What time is it, and what's the weather in Paris?"}],
)
print(resp.content[0].text)
