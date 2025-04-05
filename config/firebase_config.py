import pyrebase
import os
import json

# Firebase Configuration - renamed to match what's expected by firebase_auth.py
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyDcCZJqEBOzPiXt4qrKrWjgYcX9-kgtCNo",
    "authDomain": "mtd-malware-detection.firebaseapp.com",
    "projectId": "mtd-malware-detection",
    "storageBucket": "mtd-malware-detection.firebasestorage.app",
    "messagingSenderId": "256073377974",
    "appId": "1:256073377974:web:43ac5d147ecb1f407ede17",
    "measurementId": "G-QFWZZD2JNV",
    "databaseURL": "https://mtd-malware-detection-default-rtdb.firebaseio.com/"  # Add your database URL if you need Realtime Database
}

# Initialize Firebase
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
firebase_auth = firebase.auth()

# Path to save user data locally
USER_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.json")

def save_user(email, role, password_hash=None, user_id=None, display_name=None):
    """Save user to local storage (fallback when offline)"""
    os.makedirs(os.path.dirname(USER_DATA_PATH), exist_ok=True)
    
    # Load existing users
    users = {}
    if os.path.exists(USER_DATA_PATH):
        try:
            with open(USER_DATA_PATH, 'r') as f:
                users = json.load(f)
        except:
            users = {}
    
    # Add new user
    user_id = user_id or email.replace('@', '_').replace('.', '_')
    users[user_id] = {
        "email": email,
        "role": role,
        "display_name": display_name or email.split('@')[0],
        "password_hash": password_hash or "local_account",
        "created_at": os.path.getmtime(USER_DATA_PATH) if os.path.exists(USER_DATA_PATH) else 0
    }
    
    # Save users
    with open(USER_DATA_PATH, 'w') as f:
        json.dump(users, f, indent=2)
        
    return user_id
