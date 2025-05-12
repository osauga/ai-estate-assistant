from ollama import Client

client = Client(host='http://localhost:11434')
response = client.chat(model='llama3', messages=[{"role": "user", "content": "Hello, how are you?"}])
print(response['message']['content'])
