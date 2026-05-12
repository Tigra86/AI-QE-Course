import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_api():
    response = client.responses.create(
        model="gpt-4.1-mini",
        input="Return JSON only. Start with '{'. Explain in simple terms what output tokens are in LLM.",
        max_output_tokens=200,
        temperature=0.0
    )
    print("-" * 60)
    print("Status: "        +     response.output[0].status)
    print("Input Tokens: "  + str(response.usage.input_tokens))
    print("Output Tokens: " + str(response.usage.output_tokens))
    print("Total Tokens: "  + str(response.usage.total_tokens))
    print("-" * 60)
    print(response.output_text.strip())
    print("-" * 60)
    print(response.output)
    print("-" * 60)
    print(response.usage)
    print("-" * 60)

# ---------------------------------

call_api()