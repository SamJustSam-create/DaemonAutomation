import os
from pathlib import Path
from flask import Flask, request, jsonify, redirect, session, url_for, render_template
from dotenv import load_dotenv

load_dotenv()

import parse as schedule_parser
import calendar_api

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

# Allow HTTP for local OAuth (Google requires HTTPS in production)
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

CREDENTIALS_FILE = Path("credentials/google_creds.json")


@app.route("/")
def index():
    return render_template(
        "index.html",
        authenticated=calendar_api.is_authenticated(),
        has_credentials=CREDENTIALS_FILE.exists(),
    )


@app.route("/auth/google")
def auth_google():
    if not CREDENTIALS_FILE.exists():
        return jsonify({"error": "credentials/google_creds.json not found. See setup instructions."}), 400
    redirect_uri = url_for("auth_callback", _external=True)
    auth_url, state, code_verifier = calendar_api.get_auth_url(redirect_uri)
    session["oauth_state"] = state
    session["oauth_code_verifier"] = code_verifier
    return redirect(auth_url)


@app.route("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    if not code:
        return "OAuth error: no code received", 400
    redirect_uri = url_for("auth_callback", _external=True)
    code_verifier = session.pop("oauth_code_verifier", None)
    calendar_api.exchange_code(code, state, redirect_uri, code_verifier)
    return redirect(url_for("index"))


@app.route("/auth/status")
def auth_status():
    return jsonify({"authenticated": calendar_api.is_authenticated()})


@app.route("/parse", methods=["POST"])
def parse():
    try:
        # Image upload takes priority
        if "image" in request.files and request.files["image"].filename:
            image_file = request.files["image"]
            image_bytes = image_file.read()
            mime_type = image_file.content_type or "image/png"
            shifts = schedule_parser.parse_image(image_bytes, mime_type)
        else:
            text = request.form.get("text", "").strip()
            if not text:
                return jsonify({"error": "No text or image provided"}), 400
            shifts = schedule_parser.parse_text(text)

        if not shifts:
            return jsonify({"error": "No shifts could be parsed from the input"}), 422

        return jsonify({"shifts": shifts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/create-events", methods=["POST"])
def create_events():
    if not calendar_api.is_authenticated():
        return jsonify({"error": "Not authenticated with Google Calendar"}), 401

    data = request.get_json()
    shifts = data.get("shifts", [])
    if not shifts:
        return jsonify({"error": "No shifts provided"}), 400

    results = calendar_api.create_events(shifts)
    return jsonify({"results": results})


@app.route("/undo-events", methods=["POST"])
def undo_events():
    if not calendar_api.is_authenticated():
        return jsonify({"error": "Not authenticated with Google Calendar"}), 401
    data = request.get_json()
    event_ids = data.get("event_ids", [])
    if not event_ids:
        return jsonify({"error": "No event IDs provided"}), 400
    results = calendar_api.delete_events(event_ids)
    return jsonify({"results": results})


if __name__ == "__main__":
    import argparse
    from waitress import serve

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Run Flask dev server with auto-reload")
    args = parser.parse_args()

    if args.debug:
        app.run(debug=True, port=5000)
    else:
        print("Serving on http://localhost:5000")
        serve(app, host="127.0.0.1", port=5000)
