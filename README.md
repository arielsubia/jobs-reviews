# Jobs Reviews Dashboard

Interactive dashboard to visualize and filter job application history. Search by company, position, date range, and status with voice search support.

## Architecture

```
CVs enviados.txt → Python Parser → data.json → S3 + CloudFront → Mobile Web App
```

- **Parser:** Python script converts the notepad file into structured JSON
- **Frontend:** HTML + CSS + vanilla JS + Chart.js (static site)
- **Voice:** Native Web Speech API (Chrome/Android)
- **Infrastructure:** S3 static website + CloudFront (HTTPS)
- **Filtering:** 100% client-side, no backend required

## Local Development Setup

### Requirements

- Python 3.12+
- AWS CLI configured (for deployment)
- Chrome/Chromium browser (for voice search testing)

### Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements-dev.txt
```

### Running the Parser

```bash
python src/parser/parser.py
```

Generates `src/frontend/data.json` from `docs/CVs enviados.txt`.

> Note: The source file `docs/CVs enviados.txt` is not tracked by git. Place your own data file at that path before running the parser.

### Frontend Development

Open `src/frontend/index.html` in a browser or use a local server:

```bash
python -m http.server 8000 --directory src/frontend
```

### Tests

```bash
pytest tests/
```

### Linter

```bash
ruff check .
```

### Deployment

```bash
bash infra/deploy.sh
```

## Updating Data

1. Edit `docs/CVs enviados.txt` with new applications
2. Run the parser: `python src/parser/parser.py`
3. Re-deploy: `bash infra/deploy.sh`

## License

Proprietary — Phil Dev <sub><img src="docs/assets/logo-phildev.png" width="20"></sub>
