import json
import os

# Initialize database path
db_path = "databank.json"

# Create default databank if it doesn't exist
default_db = {
    "conversation": [],
    "facts": {},
    "name": "",
    "mood": ""
}

if not os.path.exists(db_path):
    with open(db_path, "w") as f:
        json.dump(default_db, f, indent=4)

# Load databank
def load_db():
    with open(db_path, "r") as f:
        return json.load(f)

# Save databank
def save_db(data):
    with open(db_path, "w") as f:
        json.dump(data, f, indent=4)

# Log conversation
def log_conversation(user, bot):
    db = load_db()
    db["conversation"].append({"user": user, "ava": bot})
    save_db(db)

# Analyze user input
def analyze_input(text):
    text = correct_spelling(text)
    detect_name(text)
    detect_mood(text)
    remember_facts(text)
    return text

# Detect user's name
def detect_name(text):
    db = load_db()
    triggers = ["my name is", "i am", "i'm"]
    for trig in triggers:
        if trig in text.lower():
            name = text.lower().split(trig)[-1].strip().split(" ")[0]
            db["name"] = name.capitalize()
            save_db(db)
            return name.capitalize()
    return None

# Detect user's mood
def detect_mood(text):
    db = load_db()
    moods = {
        "happy": ["happy", "great", "good", "fantastic", "fine"],
        "sad": ["sad", "bad", "terrible", "upset", "depressed"],
        "angry": ["angry", "mad", "furious", "pissed"]
    }
    for mood, keywords in moods.items():
        for word in keywords:
            if word in text.lower():
                db["mood"] = mood
                save_db(db)
                return mood
    return None

# Simple spelling correction
def correct_spelling(text):
    corrections = {
        "helo": "hello",
        "whats": "what is",
        "dont": "don't",
        "im": "i'm",
        "cant": "can't",
        "u": "you"
    }
    words = text.split()
    corrected = [corrections.get(w.lower(), w) for w in words]
    return " ".join(corrected)

# Remember user's facts
def remember_facts(text):
    db = load_db()
    if "my favorite" in text.lower():
        parts = text.lower().split("my favorite")[-1].strip().split("is")
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            db["facts"][key] = value
            save_db(db)

# Learn new responses
def auto_learn(user_input):
    db = load_db()
    if "learn:" in user_input.lower():
        try:
            parts = user_input.lower().split("learn:")[1].strip().split("=")
            question = parts[0].strip().lower()
            answer = parts[1].strip()
            db["conversation"].append({"user": question, "ava": answer})
            save_db(db)
            return f"I've learned how to respond to '{question}'."
        except:
            return "Use this format to teach me: learn: question = answer"
    return None

# Main chat loop
def chat():
    print("A.v.A is ready. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("A.v.A: Goodbye!")
            break

        response = auto_learn(user_input)
        if response:
            print("A.v.A:", response)
            log_conversation(user_input, response)
            continue

        processed = analyze_input(user_input)

        # Find matching response
        db = load_db()
        response = "I'm not sure how to respond to that yet."
        for entry in db["conversation"]:
            if entry["user"].lower() == processed.lower():
                response = entry["ava"]
                break

        # Personalize
        if db["name"]:
            response = f"{db['name']}, {response}"

        log_conversation(user_input, response)
        print("A.v.A:", response)

chat()
