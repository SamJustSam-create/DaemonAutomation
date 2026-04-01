# DaemonAutomation

A Flask web app that parses work schedules — from pasted text or screenshot images — and automatically creates Google Calendar events.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.x-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Text parsing** — paste a roster block and extract shifts via regex
- **Image parsing** — upload a schedule screenshot; Claude Vision (AI) reads it for you
- **Google Calendar integration** — creates events with title, time, role description, and invitees
- **Special uniform flag** — detects and surfaces "Special Uniform Required" shifts
- **OAuth2 PKCE flow** — secure, token-based Google authentication with no stored passwords

---

## Demo

1. Paste or upload your schedule
2. Preview the extracted shifts in a table
3. Click **Create Events** — done

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask |
| AI Parsing | Anthropic Claude (`claude-sonnet-4-6`) |
| Calendar | Google Calendar API v3 (OAuth2 PKCE) |
| Frontend | Vanilla JS + HTML/CSS (no build step) |

---

## Prerequisites

- Python 3.10 or newer
- An [Anthropic API key](https://console.anthropic.com/)
- A Google Cloud project with the **Google Calendar API** enabled and OAuth 2.0 credentials

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/SamJustSam-create/DaemonAutomation.git
cd DaemonAutomation

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Configuration

### Environment variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `FLASK_SECRET_KEY` | A random secret string for Flask sessions |

### Google OAuth credentials

**Step 1 — Create a project**

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown (top left) → **New Project**
3. Give it a name (e.g. `DaemonAutomation`) and click **Create**
4. Make sure the new project is selected in the dropdown

**Step 2 — Enable the Google Calendar API**

1. In the left sidebar go to **APIs & Services → Library**
2. Search for `Google Calendar API` and click it
3. Click **Enable**

**Step 3 — Configure the OAuth consent screen**

1. Go to **APIs & Services → OAuth consent screen**
2. Select **External** as the user type → click **Create**
3. Fill in the required fields:
   - **App name** — e.g. `DaemonAutomation`
   - **User support email** — your email address
   - **Developer contact email** — your email address
4. Click **Save and Continue** through the Scopes and Test Users screens
5. On the **Test Users** screen, click **Add Users** and add the Google account(s) you'll authenticate with
6. Click **Save and Continue** → **Back to Dashboard**

**Step 4 — Create OAuth 2.0 credentials**

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Set the application type to **Desktop app**
4. Give it a name and click **Create**
5. Click **Download JSON** on the confirmation dialog
6. Save the downloaded file to:

```
credentials/google_creds.json
```

> The `credentials/` directory is gitignored — never commit this file.

---

## Usage

```bash
# Production (default) — uses Waitress WSGI server
python app.py

# Development — enables auto-reload and debug output
python app.py --debug
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

1. **Authenticate** with Google Calendar via the "Connect Google Calendar" button
2. **Parse** your schedule:
   - **Text tab** — paste the roster text copied from your work system
   - **Image tab** — upload a screenshot of your schedule
3. **Review** the shift preview table
4. **Create Events** — events are added to your primary Google Calendar

### Event format

| Field | Value |
|---|---|
| Title | `John Doe - Work` |
| Timezone | `Australia/Melbourne` |
| Description | Role line only (e.g. `DT2:DT Intermediate - OTC`) |
| Invitees | `jane.doe@outlook.com`, `johndoe.workmail@gmail.com` |
| Breaks | Not included |

---

## Project Structure

```
DaemonAutomation/
├── app.py              # Flask routes
├── parse.py            # Text regex parser + Claude Vision image parser
├── calendar_api.py     # Google OAuth flow + Calendar event creation
├── templates/
│   └── index.html      # Frontend UI
├── static/
│   └── style.css       # Styles
├── credentials/        # Google OAuth creds (gitignored)
├── .env.example        # Environment variable template
└── requirements.txt    # Python dependencies
```

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Main UI |
| `GET` | `/auth/google` | Start Google OAuth flow |
| `GET` | `/auth/callback` | OAuth redirect handler |
| `GET` | `/auth/status` | Check authentication status |
| `POST` | `/parse` | Parse text or image into shift objects |
| `POST` | `/create-events` | Create Google Calendar events from shifts |

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a pull request

---

## License

[MIT](https://choosealicense.com/licenses/MIT)
