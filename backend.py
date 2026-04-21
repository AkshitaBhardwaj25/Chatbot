import os
from google import genai
import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import uuid

# Load .env from the same folder as this file, regardless of where you run from
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

API_KEY = os.getenv("GOOGLE_API_KEY")
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH")

# ---- Startup validation so you get a clear error instead of a cryptic one ----
if not API_KEY:
    raise EnvironmentError("GOOGLE_API_KEY not found. Check your .env file.")
if not FIREBASE_CRED_PATH:
    raise EnvironmentError("FIREBASE_CRED_PATH not found. Check your .env file.")
if not os.path.exists(FIREBASE_CRED_PATH):
    raise FileNotFoundError(
        f"Firebase credentials file not found at: '{FIREBASE_CRED_PATH}'\n"
        f"Current working directory: {os.getcwd()}\n"
        "Make sure the path in .env is correct (relative to the project root)."
    )

_db = None

def get_db():
    global _db
    if _db is None:
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CRED_PATH)
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
    return _db

def create_new_chat():
    chat_id = str(uuid.uuid4())
    get_db().collection("chats").document(chat_id).set({
        "name": "New Chat",
        "created_at": datetime.datetime.utcnow()
    })
    return chat_id

def rename_chat(chat_id, new_name):
    get_db().collection("chats").document(chat_id).update({"name": new_name})

def add_message(chat_id, role, content):
    get_db().collection("chats") \
        .document(chat_id) \
        .collection("messages") \
        .add({
            "role": role,
            "content": content,
            "time": datetime.datetime.now(datetime.timezone.utc)
        })

def get_all_chats():
    chats = get_db().collection("chats").order_by("created_at").get()
    return [(c.id, c.to_dict().get("name") or "New Chat") for c in chats]

def get_messages(chat_id):
    messages = get_db().collection("chats") \
        .document(chat_id) \
        .collection("messages") \
        .order_by("time") \
        .get()
    return [msg.to_dict() for msg in messages]

def delete_chat(chat_id):
    db_client = get_db()
    for doc in db_client.collection("chats").document(chat_id).collection("messages").get():
        doc.reference.delete()
    db_client.collection("chats").document(chat_id).delete()

def generate_ai_response(user_input, messages):
    client = genai.Client(api_key=API_KEY)
    recent_messages = messages[-10:]
    context = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
    today = datetime.datetime.now()
    formatted_date = today.strftime("%A, %d %B %Y")

    prompt = f"""You are an advanced AI assistant.

CURRENT DATE: {formatted_date}

RULES:
- If user asks today's date/day, ALWAYS use CURRENT DATE.
- Never guess dates.
- Reply in ONLY ONE language (no mixing).

Conversation:
{context}

User: {user_input}

A:
"""
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip().replace("###", "").strip()
    except Exception as e:
        return f"Something went wrong: {str(e)}"
