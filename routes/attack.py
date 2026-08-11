from flask import Blueprint, Flask, render_template, request, current_app, session
import base64
import zlib
from flask.sessions import SecureCookieSessionInterface

attack_bp = Blueprint('attack', __name__)

@attack_bp.route("/attack_sess_hijack", methods=["POST"])
def session_hijack():
    # Get session_value and security selection from form
    session_value = request.form.get("session_value")
    security_choice = request.form.get("security_choice")

    # Code from Google Gemini
    if session_value.startswith('.'):
        # If session value becomes long enough to require encryption
        payload = session_value[1:]
        
        # Pad string to be a multiple of 4 (required by base64 library)
        payload += '=' * (4 - len(payload) % 4)
        
        # 3. Decode base64 and decompress via zlib
        compressed_bytes = base64.urlsafe_b64decode(payload)
        decoded_value = zlib.decompress(compressed_bytes)
    else:
        decoded_value = base64.b64decode(session_value + '==')

    forged_value = {
        "admin_hardened": True,
        "user_fname": "Admin",
        "user_id": 1
    }

    dummy_app = Flask('dummy_app')
    dummy_app.config['SECRET_KEY'] = 'wrong-secret-key'

    if security_choice == "vulnerable":
        # If vulnerable mode, assume attacker has correctly guessed secret key
        serializer = SecureCookieSessionInterface().get_signing_serializer(current_app)
    else:
        # If hardened mode, use the dummy app with incorrect key
        serializer = SecureCookieSessionInterface().get_signing_serializer(dummy_app)

    forged_cookie = serializer.dumps(forged_value)

    return render_template("access_denied.html", showHint=True, decoded_value=decoded_value.decode('utf-8'), forged_cookie=forged_cookie)
