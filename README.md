# EzaSmart

**Quick Links:**
- **Deployed App:** https://video.kandaassist.com/login
- **GitHub:** https://github.com/Afsaumutoniwase/ezasmart
- **Demo Video:** [Add link after recording]

## Overview

EzaSmart helps farmers and hydroponics enthusiasts manage their crops by analyzing sensor data and recommending when to adjust nutrients, pH, and water.

### Why This Matters

Manual monitoring of EC, pH, and temperature is time-consuming and error-prone. Wrong adjustments lead to crop loss. EzaSmart handles this by:
- **Sensor Analysis**: Compares your measurements against 25 crop-specific ranges
- **Specific Recommendations**: Tells you exactly what to do (Add pH Up, Dilute, Add Nutrients, or Maintain)
- **Learning Hub**: Resources on hydroponics setup and best practices
- **Community Discussion**: Farmers share tips and troubleshoot together
- **Chatbot Answers**: Get immediate help with questions about your system

### Key Features

1. **Sensor API** (`POST /api/predict-sensor`)
   - Send: crop type, pH, EC, temperature
   - Get back: specific action to take (e.g., "Add_pH_Up") with explanation
   - Example: Lettuce at pH 5.0 gets "Add_pH_Up" recommendation

2. **Chatbot** (`POST /api/chat`)
   - Answer questions about nutrients, crops, and system setup
   - Works for multiple crop types and growing methods

3. **User Accounts**
   - Register and log in
   - Set up your profile with avatar
   - Reset password via email if needed

4. **Forums**
   - Organized by topic: General Discussion, System Types, Nutrient Management, Crops
   - Post questions, reply to others, share experiences
   - Post as yourself or anonymously

5. **Dashboard**
   - Quick access to sensor data and forums
   - Learning materials on hydroponics
   - Contact form for support

### Technical Stack

- **Backend**: Flask 3.0.0 with SQLAlchemy ORM
- **AI/ML**: Random Forest model for sensor prediction, Transformer-based chatbot
- **Database**: SQLite (local), deployed on PostgreSQL
- **Authentication**: Flask-Login with token-based password reset
- **Frontend**: Jinja2 templates, Bootstrap, vanilla JavaScript

## 1) Install and Run (Step by Step)

### Prerequisites

- Python 3.11 (see `runtime.txt`)
- `pip`

### Local setup (Windows PowerShell)

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`

### Optional environment variables (`.env`)

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
MAIL_DEFAULT_SENDER=your_email
MAIL_SUPPORT_RECIPIENT=your_email
```

## 2) Core Features Demonstrated

- Sensor recommendation API: `POST /api/predict-sensor`
- AI chatbot API: `POST /api/chat`
- Authentication: register, login, logout, password reset
- User profile management
- Community forums (categories, posts, replies)
- Help/contact flows

## 3) Testing Strategies and Results

### Automated tests (unit + integration)

Command:

```bash
pytest -q
```

Latest run result:

- `87 passed`
- `0 failed`
- Runtime: `29.38s`

Test Results:

- All features work as expected (87 passing tests).
- The same tests pass on both local and deployed versions.
- No failures or regressions detected.

### Functional testing with different data values

Use these examples in Postman or browser dev tools:

- Valid case (`Maintain` expected for optimal range):
  - `crop_id=Lettuce, ph_level=6.5, ec_value=1.5, ambient_temp=22`
- Low pH case (`Add_pH_Up` expected):
  - `crop_id=Tomato, ph_level=5.0, ec_value=3.0, ambient_temp=24`
- High EC case (`Dilute` expected):
  - `crop_id=Lettuce, ph_level=6.5, ec_value=3.0, ambient_temp=22`
- Validation case (`400` expected):
  - Missing `crop_id` or `ph_level`

### Performance testing across software/hardware conditions

**Screenshots to capture (store in `evidence/` folder):**

1. **Test suite run:**
   - Terminal showing `pytest -q` output: `87 passed, 0 failed` in `29.38s`

2. **Sensor API functional tests** (use Postman, browser console, or curl):
   - Request/response for **valid case** (Maintain expected):
     - Input: `crop_id=Lettuce, ph_level=6.5, ec_value=1.5, ambient_temp=22`
     - Expected response: `{"action": "Maintain", ...}`
   - Request/response for **low pH case** (Add_pH_Up expected):
     - Input: `crop_id=Tomato, ph_level=5.0, ec_value=3.0, ambient_temp=24`
     - Expected response: `{"action": "Add_pH_Up", ...}`
   - Request/response for **high EC case** (Dilute expected):
     - Input: `crop_id=Lettuce, ph_level=6.5, ec_value=3.0, ambient_temp=22`
     - Expected response: `{"action": "Dilute", ...}`

3. **Performance/deployment evidence:**
   - Browser network tab showing response time for `/api/predict-sensor` on **local** machine.
   - Browser network tab showing response time for same endpoint on **deployed** URL.
   - **Local vs deployed comparison:** document latency difference.

## 4) Analysis

- The app combines sensor recommendations, forums, and a chatbot in one place.
- Tests cover authentication, API endpoints, data models, and page routing.
- Everything tested works reliably.

## 5) Discussion (Milestones and Impact)

- Built the web app: landing page, login, dashboard, and resources.
- Added sensor analysis: checks your measurements against crop requirements.
- Added forums and chatbot: so users can learn and help each other.
- Added tests: to catch bugs and verify everything still works.

## 6) Recommendations and Future Work

- Add role-based authorization and stronger input validation.
- Add load testing for chatbot and prediction endpoints.
- Add observability (request logs, error rates, latency dashboard).
- Extend model retraining pipeline with more recent hydroponics datasets.

## 7) Deployment

### Runtime

- Python version: `3.11.9` (`runtime.txt`)

### Run command

- Local: `python app.py`
- Production (recommended): `gunicorn app:app`

### Deployment Plan (Production)

**Service:** Render

**Steps:**
1. Push code to GitHub repo.
2. Connect repo to deployment service.
3. Set environment variables (`.env` config).
4. Deploy and verify live URL.

**Deployed URL:** `https://video.kandaassist.com/login`

### Deployment verification checklist

- [ ] Landing page loads at deployed URL.
- [ ] Login/register flows work.
- [ ] Dashboard and profile render correctly after login.
- [ ] `/api/predict-sensor` returns structured JSON with valid inputs.
- [ ] `/api/chat` returns chatbot response.
- [ ] Test run on deployed environment shows same functionality as local.

## 8) Project Structure

- `app.py` main Flask app with routes, models, and AI integration
- `chatbot.py` chatbot loader and inference helper
- `tests/` automated tests (`test_api.py`, `test_auth.py`, `test_models.py`, `test_routes.py`)
- `templates/` Jinja views
- `static/` CSS, JS, images, vendor assets
- `Models/` model artifacts, notebooks, and datasets
- `evidence/` test screenshots, deployment evidence, and demo video link