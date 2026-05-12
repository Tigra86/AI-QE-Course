import os
from openai import OpenAI

# api_key = "your_api_key_here" 
# api_key = os.getenv("OPENAI_API_KEY")
# client = OpenAI(api_key=api_key)

client = OpenAI()

# sentence = "Who"
# sentence = "won"
# sentence = "Stanley"
# sentence = "Cup"
# sentence = "2025"
# sentence = "?"
sentence = "Who won Stanley Cup 2025?"

response = client.embeddings.create(
    model="text-embedding-3-small",   # or text-embedding-3-large
    input=sentence
)

embedding = response.data[0].embedding

print("\nSentence:")
print(sentence)

print("\nEmbedding vector length:", len(embedding))
print("\nEmbedding:")
print(embedding)