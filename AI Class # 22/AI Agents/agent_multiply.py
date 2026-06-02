from openai import OpenAI
import json

client = OpenAI()

tools = [
    {
        "type": "function",
        "name": "multiply",
        "description": "Multiply two numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["a", "b"],
            "additionalProperties": False
        },
        "strict": True
    }
]

def multiply(a, b):
    return a * b

input_messages = [
    {"role": "user", "content": "What is 12.5 times 4?"}
]

response = client.responses.create(
    model="gpt-4.1",
    input=input_messages,
    tools=tools
)

input_messages += response.output

for item in response.output:
    if item.type == "function_call" and item.name == "multiply":
        args = json.loads(item.arguments)
        result = multiply(**args)
        input_messages.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": str(result)
        })

final_response = client.responses.create(
    model="gpt-4.1",
    input=input_messages,
    tools=tools
)

print(final_response.output_text)