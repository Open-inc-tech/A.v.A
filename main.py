import json
import os
import re
import random
from datetime import datetime

# === CONFIG ===
db_path = "databank.json"
LOG_PATH = "chatlog.txt"
CONTEXT_LIMIT = 5

# === INIT DATABASE ===
def load_db():
    if not os.path.exists(db_path):
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# === PLACEHOLDER REPLACEMENT ===
def format_response(template, db):
    if not template:
        return ""
    result = template.replace("{name}", db.get("name", "friend"))
    result = result.replace("{mood}", db.get("mood", "okay"))
    for key, value in db.get("facts", {}).items():
        result = result.replace(f"{{facts.{key}}}", value)
    return result

# === LOGGING ===
def log_conversation(user, bot):
    db = load_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if "conversation" not in db:
        db["conversation"] = []
    db["conversation"].append({"time": timestamp, "user": user, "ava": bot})

    if "context" not in db:
        db["context"] = []
    db["context"].append({"user": user, "ava": bot})
    if len(db["context"]) > CONTEXT_LIMIT:
        db["context"].pop(0)

    save_db(db)

# === SPELLING CORRECTION ===
def correct_spelling(text, db):
    corrections = db.get("spelling_corrections", {})
    words = text.split()
    corrected = [corrections.get(w.lower(), w) for w in words]
    return " ".join(corrected)

# === DETECT NAME ===
def detect_name(text):
    db = load_db()
    match = re.search(r"\\b(my name is|i am|i'm)\\s+([A-Za-z]+)", text, re.IGNORECASE)
    if match:
        name = match.group(2).capitalize()
        db["name"] = name
        save_db(db)
        return name
    return None

# === DETECT MOOD ===
def detect_mood(text):
    db = load_db()
    for mood, keywords in db.get("moods", {}).items():
        if any(word in text.lower() for word in keywords):
            db["mood"] = mood
            save_db(db)
            return mood
    return None

# === REMEMBER FACTS ===
def remember_facts(text):
    db = load_db()
    match = re.search(r"my favorite (\\w+) is (\\w+)", text.lower())
    if match:
        key, value = match.groups()
        if "facts" not in db:
            db["facts"] = {}
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
            db.setdefault("conversation", []).append({"user": question, "ava": answer})
            save_db(db)
            return f"I've learned how to respond to '{question}'."
        except:
            return "Use this format to teach me: learn: question = answer"
    return None

# === COMMAND HANDLING ===
def process_command(text):
    db = load_db()
    commands = db.get("commands", {})

    if text == "show memory":
        facts = "\n".join([f"- {k}: {v}" for k, v in db.get("facts", {}).items()])
        return (
            f"Name: {db.get('name', 'Unknown')}\n"
            f"Mood: {db.get('mood', 'Unknown')}\n"
            f"Facts:\n{facts if facts else 'No facts saved.'}"
        )
    elif text == "clear memory":
        db["name"] = ""
        db["mood"] = ""
        db["facts"] = {}
        save_db(db)
        return "All memory has been cleared."
    elif text == "export log":
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            for entry in db.get("conversation", []):
                time = entry.get("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                f.write(f"{time} | You: {entry['user']}\n")
                f.write(f"{time} | A.v.A: {entry['ava']}\n\n")
        return f"Conversation log saved to {LOG_PATH}."
    elif text == "help":
        return "Available commands:\n" + "\n".join([f"- {cmd}: {desc}" for cmd, desc in commands.items()])
    return None

# === INTENT DETECTION ===
def detect_intent(text, db):
    for entry in db.get("conversation", []):
        if entry["user"].lower() == text.lower():
            return format_response(entry["ava"], db)
    for entry in db.get("memory", []):
        if entry["user"].lower() == text.lower():
            return format_response(entry["ava"], db)
    return None

# === CATEGORY PICKER ===
def pick_random_category(category, db):
    items = db.get("categories", {}).get(category, [])
    return format_response(random.choice(items), db) if items else ""

# === CHAT ===
def chat():
    print("🟢 A.v.A is running (Gen 3.3). Type 'exit' to quit.")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("A.v.A: Goodbye!")
            break

        db = load_db()
        user_input = correct_spelling(user_input, db)
        detect_name(user_input)
        detect_mood(user_input)
        remember_facts(user_input)

        command_result = process_command(user_input.lower())
        if command_result:
            print("A.v.A:", command_result)
            log_conversation(user_input, command_result)
            continue

        learned = auto_learn(user_input)
        if learned:
            print("A.v.A:", learned)
            log_conversation(user_input, learned)
            continue

        response = detect_intent(user_input, db)
        if not response:
            response = pick_random_category("motivation", db) if random.random() < 0.5 else "I'm not sure how to respond to that yet."

        log_conversation(user_input, response)
        print("A.v.A:", response)

if __name__ == "__main__":
    chat()
