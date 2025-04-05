import requests
import json
import os
import time
from pathlib import Path

# Import Firebase config
from config.firebase_config import FIREBASE_CONFIG, save_user

class FirebaseAuth:
    """Handle Firebase Authentication operations"""
    
    # Firebase Auth REST API endpoint
    AUTH_ENDPOINT = "https://identitytoolkit.googleapis.com/v1/accounts"
    
    def __init__(self):
        self.api_key = FIREBASE_CONFIG["apiKey"]
        self.auth_token = None
        self.auth_token_expiry = 0
        
        # Create token storage directory
        self.token_dir = Path(os.path.expanduser("~")) / ".ransomware_app"
        self.token_dir.mkdir(exist_ok=True)
        self.token_file = self.token_dir / "auth_token.json"
        
        # Try to load stored token
        self.load_auth_token()
        
    def sign_up(self, email, password, role="student"):
        """Create a new user with email and password"""
        try:
            # Firebase Auth REST API for sign up
            url = f"{self.AUTH_ENDPOINT}:signUp?key={self.api_key}"
            
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload)
            data = response.json()
            
            if response.status_code == 200 and "idToken" in data:
                # Successfully created user
                
                # Save auth token
                self.auth_token = data["idToken"]
                self.auth_token_expiry = time.time() + int(data["expiresIn"])
                self.save_auth_token()
                
                # Also save user's custom claims for role
                user_id = data["localId"]
                
                # Try to set custom claims for user role (requires separate Firebase Admin SDK) 
                # For now, we'll just save the role locally
                save_user(email, role, user_id=user_id)
                
                return {
                    "success": True,
                    "message": "User created successfully",
                    "user_id": user_id,
                    "email": email,
                    "role": role
                }
            else:
                # Handle error
                error_message = data.get("error", {}).get("message", "Unknown error")
                
                # Translate Firebase error messages to user-friendly messages
                if error_message == "EMAIL_EXISTS":
                    error_message = "The email address is already in use by another account."
                elif error_message == "OPERATION_NOT_ALLOWED":
                    error_message = "Password sign-up is disabled for this project."
                elif error_message == "TOO_MANY_ATTEMPTS_TRY_LATER":
                    error_message = "We have blocked all requests from this device due to unusual activity. Try again later."
                
                return {
                    "success": False,
                    "message": error_message
                }
                
        except requests.exceptions.ConnectionError:
            # Handle offline mode - create local account
            user_id = save_user(email, role)
            return {
                "success": True,
                "message": "User created locally (offline mode)",
                "user_id": user_id,
                "email": email,
                "role": role,
                "offline": True
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating account: {str(e)}"
            }
    
    def sign_in(self, email, password):
        """Sign in a user with email and password"""
        try:
            # Firebase Auth REST API for sign in
            url = f"{self.AUTH_ENDPOINT}:signInWithPassword?key={self.api_key}"
            
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload)
            data = response.json()
            
            if response.status_code == 200 and "idToken" in data:
                # Successfully signed in
                
                # Save auth token
                self.auth_token = data["idToken"]
                self.auth_token_expiry = time.time() + int(data["expiresIn"])
                self.save_auth_token()
                
                # Get user role from local storage
                role = self.get_user_role(email)
                
                return {
                    "success": True,
                    "message": "Sign in successful",
                    "user_id": data["localId"],
                    "email": email,
                    "role": role
                }
            else:
                # Handle error
                error_message = data.get("error", {}).get("message", "Unknown error")
                
                # Translate Firebase error messages
                if error_message == "EMAIL_NOT_FOUND":
                    error_message = "There is no user record corresponding to this email."
                elif error_message == "INVALID_PASSWORD":
                    error_message = "The password is invalid."
                elif error_message == "USER_DISABLED":
                    error_message = "The user account has been disabled."
                
                return {
                    "success": False,
                    "message": error_message
                }
                
        except requests.exceptions.ConnectionError:
            # Try offline authentication with local user data
            return self.offline_sign_in(email, password)
        except Exception as e:
            return {
                "success": False,
                "message": f"Error signing in: {str(e)}"
            }
    
    def offline_sign_in(self, email, password):
        """Authenticate against locally stored user data when offline"""
        try:
            user_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.json")
            
            if os.path.exists(user_data_path):
                with open(user_data_path, 'r') as f:
                    users = json.load(f)
                
                # Find user by email
                for user_id, user in users.items():
                    if user.get("email") == email:
                        # In a real app, we would verify the password hash
                        # For this demo, we'll accept any password in offline mode
                        return {
                            "success": True,
                            "message": "Signed in locally (offline mode)",
                            "user_id": user_id,
                            "email": email,
                            "role": user.get("role", "student"),
                            "offline": True
                        }
            
            return {
                "success": False,
                "message": "User not found in local data"
            }
        except Exception as e:
            return {
                "success": False, 
                "message": f"Error in offline sign in: {str(e)}"
            }
    
    def get_user_role(self, email):
        """Get user role from local storage"""
        try:
            user_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.json")
            
            if os.path.exists(user_data_path):
                with open(user_data_path, 'r') as f:
                    users = json.load(f)
                
                # Find user by email
                for user_id, user in users.items():
                    if user.get("email") == email:
                        return user.get("role", "student")
            
            return "student"  # Default role
        except:
            return "student"  # Default role on error
    
    def save_auth_token(self):
        """Save authentication token to file"""
        if self.auth_token:
            with open(self.token_file, 'w') as f:
                json.dump({
                    "token": self.auth_token,
                    "expiry": self.auth_token_expiry
                }, f)
    
    def load_auth_token(self):
        """Load authentication token from file"""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    
                token = data.get("token")
                expiry = data.get("expiry", 0)
                
                # Only use token if it's not expired
                if token and expiry > time.time():
                    self.auth_token = token
                    self.auth_token_expiry = expiry
            except:
                pass

    def update_email(self, current_email, current_password, new_email):
        """Update a user's email address"""
        try:
            # First verify credentials
            verify_result = self.sign_in(current_email, current_password)
            if not verify_result["success"]:
                return {"success": False, "message": "Authentication failed. Please check your current email and password."}
            
            # Check connection
            if not self._check_connection():
                return {"success": False, "message": "Internet connection is required to update email."}
            
            # Get ID token for authentication
            token_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            token_payload = {
                "email": current_email,
                "password": current_password,
                "returnSecureToken": True
            }
            
            token_response = requests.post(token_url, data=json.dumps(token_payload))
            token_data = token_response.json()
            
            if 'error' in token_data:
                return {"success": False, "message": token_data['error']['message']}
            
            id_token = token_data['idToken']
            
            # Update email with the token
            update_url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={self.api_key}"
            update_payload = {
                "idToken": id_token,
                "email": new_email,
                "returnSecureToken": True
            }
            
            update_response = requests.post(update_url, data=json.dumps(update_payload))
            update_data = update_response.json()
            
            if 'error' in update_data:
                return {"success": False, "message": update_data['error']['message']}
            
            # Update locally stored role information
            user_role = self.get_user_role(current_email)
            self._update_user_email(current_email, new_email, user_role)
            
            return {"success": True, "email": new_email}
            
        except Exception as e:
            return {"success": False, "message": f"An error occurred: {str(e)}"}
    
    def update_password(self, email, current_password, new_password):
        """Update a user's password"""
        try:
            # First verify credentials
            verify_result = self.sign_in(email, current_password)
            if not verify_result["success"]:
                return {"success": False, "message": "Authentication failed. Please check your current email and password."}
            
            # Check connection
            if not self._check_connection():
                return {"success": False, "message": "Internet connection is required to update password."}
            
            # Get ID token for authentication
            token_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            token_payload = {
                "email": email,
                "password": current_password,
                "returnSecureToken": True
            }
            
            token_response = requests.post(token_url, data=json.dumps(token_payload))
            token_data = token_response.json()
            
            if 'error' in token_data:
                return {"success": False, "message": token_data['error']['message']}
            
            id_token = token_data['idToken']
            
            # Update password with the token
            update_url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={self.api_key}"
            update_payload = {
                "idToken": id_token,
                "password": new_password,
                "returnSecureToken": True
            }
            
            update_response = requests.post(update_url, data=json.dumps(update_payload))
            update_data = update_response.json()
            
            if 'error' in update_data:
                return {"success": False, "message": update_data['error']['message']}
            
            # Update local storage if we're using offline mode
            if os.path.exists(self.credentials_file):
                try:
                    with open(self.credentials_file, 'r') as f:
                        credentials = json.load(f)
                    
                    # Update password if user exists
                    for user in credentials.get('users', []):
                        if user.get('email') == email:
                            user['password'] = new_password
                            
                    with open(self.credentials_file, 'w') as f:
                        json.dump(credentials, f)
                except:
                    pass  # Ignore errors with local storage
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "message": f"An error occurred: {str(e)}"}
            
    def _check_connection(self):
        """Check if we have an internet connection to Firebase"""
        try:
            # Make a lightweight request to check connectivity
            response = requests.head(f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}", timeout=3)
            return True
        except:
            return False
            
    def _update_user_email(self, old_email, new_email, role):
        """Update email in local role storage after email change"""
        roles_file = os.path.join(os.path.expanduser("~"), ".ransomware_app", "roles.json")
        
        try:
            if os.path.exists(roles_file):
                with open(roles_file, 'r') as f:
                    roles = json.load(f)
                    
                # Remove old email and add new one
                if old_email in roles:
                    del roles[old_email]
                    
                roles[new_email] = role
                    
                # Save updated roles
                with open(roles_file, 'w') as f:
                    json.dump(roles, f)
                    
            # Also update in offline credentials if they exist
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    credentials = json.load(f)
                    
                # Update email in users list
                for user in credentials.get('users', []):
                    if user.get('email') == old_email:
                        user['email'] = new_email
                        
                # Save updated credentials
                with open(self.credentials_file, 'w') as f:
                    json.dump(credentials, f)
                    
        except Exception as e:
            print(f"Failed to update user email: {e}")
