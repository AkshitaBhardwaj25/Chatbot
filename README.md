# 🤖 TechBlocks AI Chatbot

A conversational AI chatbot built with **Streamlit**, powered by **Google Gemini 2.5 Flash**, with persistent chat history stored in **Firebase Firestore**.

---

## Features

- **Multi-chat support** — create, switch between, and delete conversations
- **Powered by Gemini 2.5 Flash** — fast, intelligent responses
- **Firebase Firestore** — chat history persists across sessions
- **Typing animation** — smooth character-by-character response rendering
- **Dark UI** — clean dark theme with styled chat bubbles
- **Code block rendering** — syntax-highlighted code in responses
- **Auto-naming** — chats are automatically titled from your first message

---

## Project Structure

```
TechBlocks/
├── firebase_config/
│   └── your-firebase-adminsdk-*.json   # ← your Firebase credentials (never commit this)
├── backend.py                          # Firebase + Gemini logic
├── main.py                             # Streamlit UI
├── .env                                # your secrets (never commit this)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/techblocks-chatbot.git
cd techblocks-chatbot
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Firebase

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Create a project (or use an existing one)
3. Navigate to **Project Settings → Service Accounts**
4. Click **Generate new private key** — save the downloaded JSON file inside the `firebase_config/` folder
5. In Firestore, create a database in **Native mode**

### 5. Get a Gemini API key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create an API key for **Gemini**

### 6. Configure your `.env` file

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
FIREBASE_CRED_PATH=firebase_config/your-firebase-adminsdk-file.json
```

> The filename in `FIREBASE_CRED_PATH` must exactly match your downloaded JSON file.

### 7. Run the app

```bash
streamlit run main.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Requirements

```
streamlit
google-genai
firebase-admin
python-dotenv
```

Generate a full `requirements.txt` with:

```bash
pip freeze > requirements.txt
```

---

## Security

This project uses sensitive credentials. The following are **excluded from version control** via `.gitignore` and must **never be committed**:

| File / Folder | Why |
|---|---|
| `.env` | Contains your API keys |
| `firebase_config/` | Contains your Firebase private key |
| `*.json` | Catches any stray credential files |

If you accidentally push credentials, **immediately rotate them**:
- Gemini: [Google AI Studio](https://aistudio.google.com/app/apikey) → delete and recreate the key

---

## Author

Developed by **Akshita Bhardwaj**

---
