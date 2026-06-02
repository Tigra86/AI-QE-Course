from openai import OpenAI

client = OpenAI()

class SimpleAgent:
    def __init__(self):
        self.messages = [
            {"role": "system", "content": "You are a helpful teaching assistant."}
        ]

    def chat(self, user_text):
        self.messages.append({"role": "user", "content": user_text})
        response = client.responses.create(
            model="gpt-4.1",
            input=self.messages
        )
        self.messages.append({"role": "assistant", "content": response.output_text})
        return response.output_text

agent = SimpleAgent()

print(agent.chat("My name is Alex. I live in San Bruno. Remember it."))
print(agent.chat("What is my name and where I live?"))

