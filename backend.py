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

api_key = st.secrets["GOOGLE_API_KEY"]
firebase_config = st.secrets["FIREBASE_CONFIG"]

def init_db():
    if not firebase_admin._apps:
        cred = credentials.Certificate(dict(firebase_config))
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = None

def get_db():
    global db
    if db is None:
        db = init_db()
    return db

# -------------------- CREATE NEW CHAT --------------------
def create_new_chat():
    """
    Creates a new chat with a default name 'New Chat' and current timestamp.
    Returns the chat_id.
    """
    chat_id = str(uuid.uuid4())
    get_db.collection("chats").document(chat_id).set({
        "name": "New Chat",  # default name
        "created_at": datetime.datetime.utcnow()
    })
    return chat_id

# -------------------- RENAME CHAT --------------------
def rename_chat(chat_id, new_name):
    """
    Updates the chat's name.
    """
    get_db.collection("chats").document(chat_id).update({
        "name": new_name
    })

# -------------------- ADD MESSAGE --------------------
def add_message(chat_id, role, content):
    """
    Adds a message to a chat.
    """
    get_db.collection("chats") \
      .document(chat_id) \
      .collection("messages") \
      .add({
          "role": role,
          "content": content,
          "time": datetime.datetime.now(datetime.timezone.utc)
      })

# -------------------- GET ALL CHATS --------------------
def get_all_chats():
    """
    Returns a list of tuples: (chat_id, chat_name), sorted by creation time.
    """
    chats = get_db.collection("chats").order_by("created_at").get()
    chat_list = []
    for chat in chats:
        data = chat.to_dict()
        chat_name = data.get("name") or "New Chat"
        chat_list.append((chat.id, chat_name))
    return chat_list

# -------------------- GET MESSAGES --------------------
def get_messages(chat_id):
    """
    Returns all messages for a given chat, sorted by time.
    """
    messages = get_db.collection("chats") \
        .document(chat_id) \
        .collection("messages") \
        .order_by("time") \
        .get()
    return [msg.to_dict() for msg in messages]

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

Assistant:
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

# -------------------- PROCESS RESPONSE --------------------
def process_response(response):
    """
    Detect if response contains code and structure it.
    """
    if "```" in response:
        return {
            "type": "code",
            "content": response
        }
    else:
        return {
            "type": "text",
            "content": response
        }