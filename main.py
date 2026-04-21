import streamlit as st
import time
from backend import (
    generate_ai_response, create_new_chat, add_message,
    get_all_chats, get_messages, rename_chat, delete_chat
)

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

.chat-container {
    max-width: 800px;
    margin: auto;
}

.user-bubble {
    background-color: #0f4c81;
    color: white;
    padding: 12px 16px;
    border-radius: 12px;
    margin: 8px 0;
    text-align: right;
}

.bot-bubble {
    background-color: #2d333b;
    color: white;
    padding: 12px 16px;
    border-radius: 12px;
    margin: 8px 0;
    text-align: left;
}

.sidebar-title {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 10px;
}

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

# -------------------- TYPING EFFECT --------------------
def stream_response(text):
    placeholder = st.empty()
    typed = ""
    for char in text:
        typed += char
        placeholder.markdown(f"<div class='bot-bubble'>🤖 {typed}</div>", unsafe_allow_html=True)
        time.sleep(0.005)

# -------------------- DETECT CODE LANGUAGE --------------------
def extract_code_blocks(text):
    """
    Returns a list of segments: each is either
      {"type": "text", "content": "..."}  or
      {"type": "code", "lang": "python", "content": "..."}
    """
    segments = []
    while "```" in text:
        before, rest = text.split("```", 1)
        if before:
            segments.append({"type": "text", "content": before})
        # rest starts with optional language then newline
        lines = rest.split("\n", 1)
        lang = lines[0].strip() or "text"
        code_and_after = lines[1] if len(lines) > 1 else ""
        if "```" in code_and_after:
            code, text = code_and_after.split("```", 1)
            segments.append({"type": "code", "lang": lang, "content": code.strip()})
        else:
            # No closing fence — treat the rest as code
            segments.append({"type": "code", "lang": lang, "content": code_and_after.strip()})
            text = ""
    if text:
        segments.append({"type": "text", "content": text})
    return segments

def render_response(text, animate=False):
    """Render a response, handling mixed text + code blocks."""
    segments = extract_code_blocks(text)
    if len(segments) == 1 and segments[0]["type"] == "text":
        if animate:
            stream_response(text)
        else:
            st.markdown(f"<div class='bot-bubble'>🤖 {text}</div>", unsafe_allow_html=True)
    else:
        for seg in segments:
            if seg["type"] == "code":
                st.code(seg["content"], language=seg["lang"])
            else:
                st.markdown(f"<div class='bot-bubble'>{seg['content']}</div>", unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">💬 Chats</div>', unsafe_allow_html=True)

    if st.button("➕ New Chat"):
        st.session_state.current_chat = create_new_chat()
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    chats = get_all_chats()  # list of (chat_id, chat_name)

    if not chats:
        st.info("No chats yet. Start a new chat!")
    else:
        st.markdown('<div class="chat-list">', unsafe_allow_html=True)

        for chat_id, chat_name in reversed(chats):
            chat_label = chat_name or f"Chat {chat_id[:5]}"
            col1, col2 = st.columns([4, 1])

            with col1:
                if st.button(f"💬 {chat_label}", key=f"switch_{chat_id}"):
                    st.session_state.current_chat = chat_id
                    st.session_state.messages = get_messages(chat_id)
                    st.rerun()

            with col2:
                if st.button("🗑️", key=f"delete_{chat_id}"):
                    # Properly delete subcollection + document
                    delete_chat(chat_id)

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
        st.markdown(f"<div class='user-bubble'>👤 {msg['content']}</div>", unsafe_allow_html=True)
    else:
        render_response(msg["content"], animate=False)

st.markdown('</div>', unsafe_allow_html=True)

# -------------------- INPUT --------------------
if prompt := st.chat_input("Type your message..."):

    if not st.session_state.current_chat:
        st.session_state.current_chat = create_new_chat()
        st.session_state.messages = []

    # Save + display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    add_message(st.session_state.current_chat, "user", prompt)

    # Auto-rename chat on first message
    if len(st.session_state.messages) == 1:
        chat_title = prompt[:30] + "..." if len(prompt) > 30 else prompt
        rename_chat(st.session_state.current_chat, chat_title)

    st.markdown(f"<div class='user-bubble'>👤 {prompt}</div>", unsafe_allow_html=True)

    # Generate + save AI response
    with st.spinner("Thinking..."):
        response = generate_ai_response(prompt, st.session_state.messages)

    add_message(st.session_state.current_chat, "assistant", response)
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Render with animation
    render_response(response, animate=True)