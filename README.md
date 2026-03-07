# EzaSmart

Minimal Flask platform for hydroponics support, monitoring, learning resources, and an AI chatbot.

## Quick Start

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5000`

## Configuration

Create a `.env` file for mail/password reset features.

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

## Project Layout

- `app.py` — main Flask app (routes, auth, DB models, AI integration).
- `chatbot.py` — standalone EzaSmart RAG chatbot loader/inference helper.
- `requirements.txt` — Python dependencies.
- `pytest.ini` — pytest settings.
- `runtime.txt` — runtime pin for deployment.
- `instance/` — local runtime data (SQLite DB and instance files).
- `Models/` — AI assets, training notebooks, datasets, and model artifacts:
  - `ai_nutrient_analysis/` — nutrient prediction training notebook + metadata.
  - `chatbot/` — chatbot model artifacts + metadata.
  - `Growmate/` — tokenizer/model config files.
  - `Kaggle data/` — raw/cleaned datasets.
  - `scrape_*.py` + `*_knowledge.json` + `*_qa_data.json` — knowledge/data builders.
- `static/` — frontend assets:
  - `css/` — page styles.
  - `js/` — client scripts.
  - `img/` — uploaded/static images.
  - `vendor/`, `vendor2/` — third-party frontend libraries.
- `templates/` — Jinja2 HTML views/pages and shared UI blocks.
- `tests/` — API/auth/model/route test suite and test fixtures.
- `__pycache__/` — Python bytecode cache.

## Tests

```bash
pytest -q
```

## Notes

- Default database is SQLite (`sqlite:///database.db`).
- Some AI model files are large and loaded from `Models/` at runtime.