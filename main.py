import streamlit as st
import time
from backend import generate_ai_response, create_new_chat, add_message, get_all_chats, get_messages
from backend import rename_chat
import datetime

# -------------------- CONFIG --------------------
st.set_page_config(page_title="AI Chatbot", layout="wide")

# -------------------- SESSION STATE --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

# -------------------- CSS / DARK UI --------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0e1117;
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

/* Chat bubbles */
.chat-container {
    max-width: 800px;
    margin: auto;
}

.user {
    background-color: #0f4c81;  /* darker blue */
    color: white;
    padding: 12px;
    border-radius: 12px;
    margin: 8px 0;
    text-align: right;
}

.bot {
    background-color: #2d333b;
    color: white;
    padding: 12px;
    border-radius: 12px;
    margin: 8px 0;
    text-align: left;
}

/* Sidebar */
.sidebar-title {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# -------------------- TYPING EFFECT FUNCTION --------------------
def stream_response(text):
    placeholder = st.empty()
    typed = ""

    for char in text:
        typed += char
        placeholder.markdown(f"<div class='bot'>🤖 {typed}</div>", unsafe_allow_html=True)
        time.sleep(0.005)  # faster + smoother

def format_text(text):
    # Convert **bold** → <b>bold</b>
    while "**" in text:
        text = text.replace("**", "<b>", 1)
        text = text.replace("**", "</b>", 1)
    return text

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">💬 Chats</div>', unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.current_chat = create_new_chat()
        st.session_state.messages = []

    st.markdown("---")

    chats = get_all_chats()  # list of (chat_id, chat_name)
    if not chats:
        st.info("No chats yet. Start a new chat!")
    else:
        # Scrollable chat container
        st.markdown("""
        <style>
        .chat-list {
            max-height: 400px;
            overflow-y: auto;
            padding-right: 5px;
        }
        .chat-item {
            padding: 6px;
            margin-bottom: 4px;
            border-radius: 6px;
            transition: background-color 0.2s;
        }
        .chat-item:hover {
            background-color: #2d333b;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="chat-list">', unsafe_allow_html=True)

        for chat_id, chat_name in reversed(chats):
            chat_label = chat_name or f"Chat {chat_id[:5]}"
            col1, col2 = st.columns([4,1])
            with col1:
                if st.button(f"💬 {chat_label}", key=f"switch_{chat_id}"):
                    st.session_state.current_chat = chat_id
                    st.session_state.messages = get_messages(chat_id)
            with col2:
                if st.button("🗑️", key=f"delete_{chat_id}"):
                    from backend import db
                    db.collection("chats").document(chat_id).delete()

                    # Reset current chat if deleted
                    if st.session_state.current_chat == chat_id:
                        st.session_state.current_chat = None
                        st.session_state.messages = []

                    st.toast("Chat deleted")

                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# -------------------- TITLE --------------------
st.markdown("<h1 style='text-align:center;'>🤖 AI Chatbot</h1>", unsafe_allow_html=True)

# -------------------- CHAT DISPLAY --------------------
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='user'>👤 {msg['content']}</div>", unsafe_allow_html=True)
    else:
        # ✅ Let Streamlit render markdown properly
        with st.container():
            st.markdown("<div class='bot'>", unsafe_allow_html=True)
            st.markdown(msg["content"])   # <-- THIS FIXES EVERYTHING
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# -------------------- INPUT --------------------
if prompt := st.chat_input("Type your message..."):

    if not st.session_state.current_chat:
        st.session_state.current_chat = create_new_chat()
        st.session_state.messages = []

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    add_message(st.session_state.current_chat, "user", prompt)

    # Auto rename chat (only first message)
    if len(st.session_state.messages) == 1:
        chat_title = prompt[:30] + "..." if len(prompt) > 30 else prompt
        rename_chat(st.session_state.current_chat, chat_title)

    # Display instantly
    st.markdown(f"<div class='user'>👤 {prompt}</div>", unsafe_allow_html=True)

    # Generate AI response
    response = generate_ai_response(prompt, st.session_state.messages)
    add_message(st.session_state.current_chat, "assistant", response)

    # Typing animation for AI
    if "```" in response:
        code = response.split("```")[1]
        code = code.replace("python", "").strip()
        st.code(code, language="python")
    else:
        stream_response(response)

    # Save AI response in session
    st.session_state.messages.append({"role": "assistant", "content": response})