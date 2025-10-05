from flask import Flask, request, jsonify, send_from_directory
from huggingface_hub import InferenceClient
from flask_cors import CORS
import json
import time

INFO_PATH = 'hackathon-sstorytelling\\api.json'
TOKEN_PATH = 'hackathon-sstorytelling\\api.json'
MIN_TIME = 3
MAX_USAGE = 15
MODEL = "meta-llama/Llama-3.2-1B-Instruct"


MODEL_PROMPT = {"role": "system", "content": "You are WAVES, A friendly chatbot that is being used by a website for explaining Solar weather to people as easy as possible, Your goal is to be as explanatory as possible while ignoring or rejecting any unrelated question"}

with open(TOKEN_PATH, 'r') as f:
    tokens = json.load(f)

client = InferenceClient(
    model=MODEL,
    token=tokens['hf_token']
)

def predict(chat_history):
    """
    chat_history: list of messages, each message is { "role": "system" / "user" / "assistant", "content": "..." }
    """
    chat_history.insert(0, MODEL_PROMPT)
    print(chat_history)
    resp = client.chat_completion(
        messages=chat_history
    )
    # resp.choices[0].message is the assistant reply
    return resp.choices[0].message.content

class DDoS_check():
    def __init__(self) -> None:
        try:
            with open(INFO_PATH, 'r') as f:
                data = json.load(f)
                self.messages = data.get("messages", {})
                self.recent_messages = data.get("recent_messages", {})
                self.ip_usage = data.get("ip_usage", {})
        except FileNotFoundError:
            # file doesn't exist yet, start fresh
            self.messages = {}
            self.recent_messages = {}
            self.ip_usage = {}


    def save_ds(self):
        with open(INFO_PATH, 'w') as f:
            json.dump({"messages":self.messages, "recent_messages":self.recent_messages, "ip_usage":self.ip_usage}, f)
    
    def check(self, message, ip):
        last_time = self.recent_messages.get(ip, MIN_TIME+1)
        if time.time() - last_time < MIN_TIME:
            self.recent_messages
            return False, ""
        else:
            if self.ip_usage.get(ip, 0) > MAX_USAGE:
                return False, ""
            else:
                try:
                    self.ip_usage[ip] += 1
                except:
                    self.ip_usage[ip] = 1
                self.recent_messages[ip] = time.time()
                return True, predict(message)

d_check = DDoS_check()


app = Flask(__name__)
CORS(app)  # allow cross-origin requests

@app.route('/api/messages', methods=['POST'])
def post_message():
    data = request.json
    if not isinstance(data, list):
        return jsonify({"error": "Invalid message format"}), 400

    client_ip = request.remote_addr
    raw_message = data

    print(f"[{client_ip}] : {raw_message}")
    result = d_check.check(raw_message, client_ip)
    print(f"To Give: {result}")

    processed_message = f"{client_ip} says: {raw_message}"
    
    if processed_message[0]:
        return jsonify(result[1])       # The only thing that the thing reutrns is processed so keep that in mind
    else:
        return jsonify("Woops smt went wrong...")

if __name__ == '__main__':
    app.run(debug=True)