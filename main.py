import json
import os
import re
from datetime import datetime

# === CONFIG ===
DB_PATH = "databank.json"
LOG_PATH = "chatlog.txt"
CONTEXT_LIMIT = 5

# === DEFAULT DATABASE ===
default_db = {
    "conversation": [],
    "facts": {},
    "name": "",
    "mood": "",
    "context": []
}

# === INIT DATABASE ===
if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w") as f:
        json.dump(default_db, f, indent=4)

# === LOAD & SAVE DB ===
def load_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=4)

# === LOGGING ===
def log_conversation(user, bot):
    db = load_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db["conversation"].append({"time": timestamp, "user": user, "ava": bot})

    # Context memory update
    db["context"].append({"user": user, "ava": bot})
    if len(db["context"]) > CONTEXT_LIMIT:
        db["context"].pop(0)

    save_db(db)

# === SPELLING CORRECTION ===
def correct_spelling(text):
    corrections = {
        "helo": "hello", "whats": "what is", "dont": "don't",
        "im": "i'm", "cant": "can't", "u": "you", "pls": "please",
        "thx": "thanks", "tnx": "thanks", "fav": "favorite"
    }
    words = text.split()
    corrected = [corrections.get(w.lower(), w) for w in words]
    return " ".join(corrected)

# === DETECT NAME ===
def detect_name(text):
    db = load_db()
    match = re.search(r"\b(my name is|i am|i'm)\s+([A-Za-z]+)", text, re.IGNORECASE)
    if match:
        name = match.group(2).capitalize()
        db["name"] = name
        save_db(db)
        return name
    return None

# === DETECT MOOD ===
def detect_mood(text):
    db = load_db()
    moods = {
        "happy": ["happy", "great", "good", "fantastic", "fine"],
        "sad": ["sad", "bad", "terrible", "upset", "depressed"],
        "angry": ["angry", "mad", "furious", "pissed"]
    }
    for mood, keywords in moods.items():
        if any(word in text.lower() for word in keywords):
            db["mood"] = mood
            save_db(db)
            return mood
    return None

# === REMEMBER FACTS ===
def remember_facts(text):
    db = load_db()
    match = re.search(r"my favorite (\w+) is (\w+)", text.lower())
    if match:
        key, value = match.groups()
        db["facts"][key] = value
        save_db(db)

# === AUTO LEARNING ===
def auto_learn(user_input):
    db = load_db()
    if "learn:" in user_input.lower():
        try:
            parts = user_input.split("learn:")[1].strip().split("=")
            question = parts[0].strip().lower()
            answer = parts[1].strip()
            db["conversation"].append({"user": question, "ava": answer})
            save_db(db)
            return f"I've learned how to respond to '{question}'."
        except:
            return "Use this format to teach me: learn: question = answer"
    return None

# === DETECT INTENT ===
def detect_intent(text):
    text = text.lower()
    if any(word in text for word in ["hello", "hi", "hey"]):
        return "Hello! How can I help you?"
    if "thank" in text:
        return "You're welcome!"
    if any(word in text for word in ["bye", "goodbye", "see you"]):
        return "Goodbye! Take care!"
    return None

# === COMMANDS ===
def process_command(text):
    db = load_db()
    if text == "show memory":
        facts = "\n".join([f"- {k}: {v}" for k, v in db["facts"].items()])
        return (
            f"Name: {db['name'] or 'Unknown'}\n"
            f"Mood: {db['mood'] or 'Unknown'}\n"
            f"Facts:\n{facts if facts else 'No facts saved.'}"
        )
    elif text == "clear memory":
        save_db(default_db.copy())
        return "All memory has been cleared."
    elif text == "export log":
        with open(LOG_PATH, "w") as f:
            for entry in db["conversation"]:
                f.write(f"{entry['time']} | You: {entry['user']}\n")
                f.write(f"{entry['time']} | A.v.A: {entry['ava']}\n\n")
        return f"Conversation log saved to {LOG_PATH}."
    return None

# === QUESTION / COMMAND DETECTION ===
def analyze_input_type(text):
    if text.endswith("?") or re.match(r"(what|who|why|how|when|where)\b", text.lower()):
        return "question"
    elif re.match(r"(tell|show|say|give|do|make|remind|list|open)\b", text.lower()):
        return "command"
    else:
        return "statement"

# === CONTEXTUAL RESPONSE HELP ===
def get_last_topic():
    db = load_db()
    if db["context"]:
        last = db["context"][-1]
        return last["user"]
    return None

# === ANALYZE INPUT ===
def analyze_input(text):
    text = correct_spelling(text)
    detect_name(text)
    detect_mood(text)
    remember_facts(text)
    return text

# === MAIN CHAT ===
def chat():
    print("🟢 A.v.A is running (Gen 3.2). Type 'exit' to quit.")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("A.v.A: Goodbye!")
            break

        # Special commands
        command_result = process_command(user_input.lower())
        if command_result:
            print("A.v.A:", command_result)
            log_conversation(user_input, command_result)
            continue

        # Learning new response
        learned = auto_learn(user_input)
        if learned:
            print("A.v.A:", learned)
            log_conversation(user_input, learned)
            continue

        # Analyze + prepare response
        processed = analyze_input(user_input)
        input_type = analyze_input_type(processed)
        db = load_db()
        response = None

        # Check for matching learned input
        for entry in db["conversation"]:
            if entry["user"].lower() == processed.lower():
                response = entry["ava"]
                break

        # Context fallback
        if not response and input_type == "question":
            last_topic = get_last_topic()
            if last_topic:
                response = f"You mentioned '{last_topic}'. Can you tell me more?"
        
        # Intent fallback
        if not response:
            response = detect_intent(processed)

        # Final fallback
        if not response:
            response = "I'm not sure how to respond to that yet."

        # Personalization
        if db["name"]:
            response = f"{db['name']}, {response}"

        log_conversation(user_input, response)
        print("A.v.A:", response)

# === RUN ===
if __name__ == "__main__":
    chat()
