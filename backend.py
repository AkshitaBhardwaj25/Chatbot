import os
from google import genai
import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import streamlit as st
import json

api_key = st.secrets["GOOGLE_API_KEY"]
firebase_config = st.secrets["FIREBASE_CONFIG"]

_db = None  # renamed to avoid shadowing the module-level `db` export

def init_db():
    if not firebase_admin._apps:
        firebase_dict = json.loads(firebase_config)
        firebase_dict["private_key"] = firebase_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(firebase_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def get_db():
    global _db
    if _db is None:
        _db = init_db()
    return _db

# Expose `db` as a property-like accessor so `from backend import db` still works.
# Frontend uses `backend.db` directly for deletes — route it through get_db() instead.
@property
def db():
    return get_db()

# -------------------- CREATE NEW CHAT --------------------
def create_new_chat():
    chat_id = str(uuid.uuid4())
    get_db().collection("chats").document(chat_id).set({
        "name": "New Chat",
        "created_at": datetime.datetime.utcnow()
    })
    return chat_id

# -------------------- RENAME CHAT --------------------
def rename_chat(chat_id, new_name):
    get_db().collection("chats").document(chat_id).update({
        "name": new_name
    })

# -------------------- ADD MESSAGE --------------------
def add_message(chat_id, role, content):
    get_db().collection("chats") \
        .document(chat_id) \
        .collection("messages") \
        .add({
            "role": role,
            "content": content,
            "time": datetime.datetime.now(datetime.timezone.utc)
        })

# -------------------- GET ALL CHATS --------------------
def get_all_chats():
    chats = get_db().collection("chats").order_by("created_at").get()
    chat_list = []
    for chat in chats:
        data = chat.to_dict()
        chat_name = data.get("name") or "New Chat"
        chat_list.append((chat.id, chat_name))
    return chat_list

# -------------------- GET MESSAGES --------------------
def get_messages(chat_id):
    messages = get_db().collection("chats") \
        .document(chat_id) \
        .collection("messages") \
        .order_by("time") \
        .get()
    return [msg.to_dict() for msg in messages]

# -------------------- GENERATE AI RESPONSE --------------------
def generate_ai_response(user_input, messages):
    client = genai.Client(api_key=api_key)

    recent_messages = messages[-10:]
    context = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])

    today = datetime.datetime.now()
    formatted_date = today.strftime("%A, %d %B %Y")

    prompt = f"""
You are an advanced AI assistant.

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
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        text = text.replace("###", "").strip()
        return text

    except Exception as e:
        return f"Something went wrong: {str(e)}"

# -------------------- DELETE CHAT --------------------
def delete_chat(chat_id):
    """
    Deletes all messages in a chat subcollection, then the chat document itself.
    Firestore does NOT auto-delete subcollections, so we must do it manually.
    """
    db_client = get_db()
    messages_ref = db_client.collection("chats").document(chat_id).collection("messages")
    docs = messages_ref.get()
    for doc in docs:
        doc.reference.delete()
    db_client.collection("chats").document(chat_id).delete()
