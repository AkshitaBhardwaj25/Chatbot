from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import firestore , credentials

load_dotenv()
firekey = os.getenv("FIREBASE_CONFIG_KEY")
cred = credentials.Certificate(firekey)
app = firebase_admin.initialize_app(cred)
db = firestore.client()

print("firekey: ", firekey)