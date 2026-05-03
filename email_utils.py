# email_utils.py - Update this file on your computer
import random
import string
import threading
import requests
from kivy.clock import Clock

# ============================================
# MUST MATCH THE SECRET_KEY IN GOOGLE SCRIPT!
# ============================================
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzE8qr7oZIDl1DdGTsTkWoXfHXqPtxml3XAaVx1pfPsEWKcESf2LV89o6V--7VrMFuG/exec"
SECRET_KEY = "TutorApp2024!@#"  # <-- MUST MATCH Google Script!


def generate_verification_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


def send_verification_email(recipient_email, verification_code):
    try:
        data = {
            "email": recipient_email,
            "code": verification_code,
            "secret": SECRET_KEY  # This must match!
        }

        response = requests.post(
            WEBAPP_URL,
            json=data,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            return result.get('success', False)
        return False

    except Exception as e:
        print(f"Error: {e}")
        return False


def send_verification_email_async(recipient_email, verification_code, callback=None):
    def send():
        success = send_verification_email(recipient_email, verification_code)
        if callback:
            Clock.schedule_once(lambda dt: callback(success))

    thread = threading.Thread(target=send)
    thread.daemon = True
    thread.start()


def send_verification_email_safe(recipient_email, verification_code, callback=None):
    return send_verification_email_async(recipient_email, verification_code, callback)