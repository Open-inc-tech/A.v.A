import json
import os
import re
import random
from datetime import datetime

# === CONFIGURATION ===
CONFIG = {
    "DB_PATH": "databank.json",
    "LOG_PATH": "chatlog.txt",
    "CONTEXT_LIMIT": 5,
    "DEFAULT_NAME": "friend",
    "DEFAULT_MOOD": "okay",
    "ENCODING": "utf-8"
}

# === DATABASE HANDLING ===
def load_db():
    path = CONFIG["DB_PATH"]
    if not os.path.exists(path):
        with open(path, "w", encoding=CONFIG["ENCODING"]) as f:
            json.dump({}, f, indent=4)
    with open(path, "r", encoding=CONFIG["ENCODING"]) as f:
        return json.load(f)

def save_db(data):
    path = CONFIG["DB_PATH"]
    with open(path, "w", encoding=CONFIG["ENCODING"]) as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# === ADVANCED PLACEHOLDER REPLACEMENT ===
def format_response(template, db):
    if not template:
        return ""

    def get_nested_value(path, data):
        for key in path.split('.'):
            if isinstance(data, dict):
                data = data.get(key, None)
            else:
                return None
        return data

    placeholders = re.findall(r"\{([^}]+)\}", template)
    for placeholder in placeholders:
        value = get_nested_value(placeholder, db)
        if value is not None:
            template = template.replace(f"{{{placeholder}}}", str(value))

    return template

# === LOGGING ===
def log_conversation(user, bot):
    db = load_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.setdefault("conversation", []).append({"time": timestamp, "user": user, "ava": bot})
    db.setdefault("context", []).append({"user": user, "ava": bot})
    
    while len(db["context"]) > CONFIG["CONTEXT_LIMIT"]:
        db["context"].pop(0)

    save_db(db)

# === SPELLING CORRECTION ===
def correct_spelling(text, db):
    corrections = db.get("spelling_corrections", {})
    return " ".join([corrections.get(word.lower(), word) for word in text.split()])

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
        db.setdefault("facts", {})[key] = value
        save_db(db)

# === AUTO LEARNING (Improved) ===
def auto_learn(user_input):
    db = load_db()
    if "learn:" in user_input.lower():
        try:
            content = user_input.split("learn:", 1)[1].strip()
            if "=" not in content:
                return "❌ Incorrect format. Use: learn: question = answer"

            question, answer = map(str.strip, content.split("=", 1))
            question = question.lower()

            updated = False
            for entry in db.get("conversation", []):
                if entry["user"].lower() == question:
                    entry["ava"] = answer
                    updated = True
                    break

            if not updated:
                db.setdefault("conversation", []).append({"user": question, "ava": answer})

            save_db(db)
            return f"✅ I've {'updated' if updated else 'learned'} how to respond to '{question}'."
        except Exception as e:
            return f"⚠️ Error while learning: {e}"
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
        with open(CONFIG["LOG_PATH"], "w", encoding=CONFIG["ENCODING"]) as f:
            for entry in db.get("conversation", []):
                time = entry.get("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                f.write(f"{time} | You: {entry['user']}\n")
                f.write(f"{time} | A.v.A: {entry['ava']}\n\n")
        return f"Conversation log saved to {CONFIG['LOG_PATH']}."
    elif text == "help":
        return "Available commands:\n" + "\n".join([f"- {cmd}: {desc}" for cmd, desc in commands.items()])
    return None

# === INTENT DETECTION (SMARTER) ===
def detect_intent(text, db):
    user_input = text.lower()

    def match(entry):
        if entry["user"].lower() == user_input:
            return True
        for alt in entry.get("alternatives", []):
            if alt.lower() == user_input:
                return True
        return False

    for entry in reversed(db.get("conversation", [])):  # latest first
        if match(entry):
            return format_response(entry["ava"], db)

    for entry in reversed(db.get("memory", [])):
        if match(entry):
            return format_response(entry["ava"], db)

    # Optional: fuzzy matching can go here
    return None


# === CATEGORY PICKER (SAFE & RANDOMIZED) ===
def pick_random_category(category, db):
    items = db.get("categories", {}).get(category, [])
    if not items:
        return f"⚠️ No items found in category '{category}'."

    response_template = random.choice(items)
    return format_response(response_template, db)

# === ERROR HANDLING SYSTEM ===
def handle_error(error, code="ERR_UNKNOWN"):
    error_message = f"❗ Error [{code}]: {str(error)}"
    print(f"A.v.A: {error_message}")
    
    # Optional: log to separate file
    with open("errorlog.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp} | {code} | {str(error)}\n")

# === MAIN CHAT ===
def chat():
    print("🟢 A.v.A is running (Gen 3.3.6). Type 'exit' to quit.")
    while True:
        try:
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

        except Exception as e:
            handle_error(e, code="ERR_CHAT_PROCESSING")

if __name__ == "__main__":
    chat()
