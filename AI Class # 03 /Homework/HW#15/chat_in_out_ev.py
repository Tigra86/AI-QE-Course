import requests
import json
import os

url =       "https://api.openai.com/v1/chat/completions"
model =     "gpt-3.5-turbo"
API_KEY =   os.environ.get('OPENAI_API_KEY')
iterate =   3

headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer ' + API_KEY
}

with open('prompts.txt', 'r', encoding='utf-8') as prompt_file:
    prompts = [line.strip() for line in prompt_file if line.strip()]

for prompt in prompts:

    for i in range(iterate):
        payload = json.dumps({"model": model,"messages": [{"role": "user", "content": prompt}]})
        
        response = requests.post(url, headers=headers, data=payload)
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        with open('content.txt', 'a', encoding='utf-8-sig') as f:
            f.write(content + '\n')
        
        print(f"Processed iteration {i+1}/{iterate}: '{prompt}'")

print("All contents saved to content.txt")