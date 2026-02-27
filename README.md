# Fake News Credibility Assessment Engine (rAIson)

A lightweight, explainable credibility screening system built with **Python + Streamlit** and powered by **rAIson (ai-raison.com)** decision policies.

This project does NOT attempt to prove factual truth. 
Instead, it detects credibility-related signals and applies structured argumentation 
policies to classify content as:

- **credible**
- **needs verification**
- **likely misinformation**

---

## Project Structure

```text
Fake-News-Credibility-Assessment-Engine/
└── fnce/
    ├── app.py              # Main Streamlit application interface
    ├── config.py           # Configuration and environment loading
    ├── core/
    │   ├── extractor.py    # NLP signal extraction logic
    │   ├── decision.py     # rAIson policy integration
    │   ├── raison_client.py # API client for rAIson communication
    │   └── schema.py       # Data models and validation schemas
    ├── data/
    │   ├── lexicons.json   # Keyword/pattern dictionaries for NLP
    │   ├── source_domains.json # Trusted and untrusted domain databases
    │   └── demo_cases.json # Sample data for testing and demonstrations
    ├── utils/              # Helper functions and formatting tools
    └── tests/              # Pytest suite for core logic

```

### 2. Enter the project directory

```bash
cd fnce
```

### 3. Create a virtual environment (recommended)

Windows:
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file inside the `fnce/` directory:

```
RAISON_API_KEY=YOUR_KEY_HERE
RAISON_API_URL=YOUR_EXECUTION_ENDPOINT_HERE
```

Do NOT commit `.env` to GitHub.

---

## Run the Application

From inside `fnce/`:

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal (usually http://localhost:8501).

---

## How It Works

1. User submits title and article text.
2. Rule-based NLP detects:
   - Clickbait patterns
   - Emotional language
   - Verifiable sources (URL / DOI)
   - Unsupported claims
3. Signals are converted into predefined rAIson element IDs.
4. rAIson applies decision policies.
5. Final classification is displayed in the interface.

---

## Testing

From inside `fnce/`:

```bash
pytest -q
```

---

## Author

Moussamb Mohamed Oussein  
Master 2 – Distributed Artificial Intelligence  
Université Paris Cité
