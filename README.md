# Jobs Reviews Dashboard

Interactive dashboard to visualize and filter job application history. Search by company, position, date range, and status with voice search support.

## Architecture

```mermaid
graph LR
    A[CVs enviados.txt] --> B[Python Parser]
    B --> C[data.json]
    C --> D[S3 Bucket]
    D --> E[CloudFront CDN]
    E --> F[Mobile Web App]
    F --> G[Filters + Voice Search]
    G --> H[Dashboard + Charts]
```

- **Parser:** Python script converts the notepad file into structured JSON
- **Frontend:** HTML + CSS + vanilla JS + Chart.js (static site, mobile-first)
- **Voice:** Native Web Speech API (Chrome/Android, es-AR)
- **Infrastructure:** S3 static website + CloudFront (HTTPS)
- **Filtering:** 100% client-side, instant, no backend required

## Features

- Filter by company, position, status, and date range (all combinable)
- Voice search via microphone button (Chrome/Android)
- Metrics: total applications, rejected, favorites, pending, rejection rate
- Bar chart: applications per month
- Doughnut chart: distribution by status
- Top 10 companies with most interactions
- Clickable company list for quick filtering
- Responsive design optimized for mobile

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
python -m src.parser.parser
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

```powershell
powershell -ExecutionPolicy Bypass -File infra/deploy.ps1
```

The deploy script is idempotent (safe to run multiple times). It will:
1. Create/verify the S3 bucket
2. Upload frontend files with correct content-types
3. Create or invalidate CloudFront distribution
4. Print the final URL

## Updating Data

1. Edit `docs/CVs enviados.txt` with new applications
2. Run the parser: `python -m src.parser.parser`
3. Re-deploy: `powershell -ExecutionPolicy Bypass -File infra/deploy.ps1`

## License

Proprietary — Phil Dev <sub><img src="docs/assets/logo-phildev.png" width="20"></sub>
