# HR Parser

A comprehensive HR parsing system that converts resumes and job descriptions into canonical JSON format using GPT-4o-mini, with MongoDB storage and intelligent scoring capabilities.

## Project Structure

```
hr-parser/
├── src/                    # Source code
│   ├── hr_parser/         # Core HR parsing package
│   │   ├── __init__.py
│   │   ├── config.py      # Configuration management
│   │   ├── extractor.py   # File text extraction
│   │   ├── gpt_client.py  # OpenAI GPT integration
│   │   ├── schemas.py     # Pydantic data models
│   │   ├── service.py     # Core parsing service
│   │   ├── repository.py  # MongoDB operations
│   │   └── router.py      # FastAPI routes
│   └── app/               # Web application
│       ├── main.py        # FastAPI app entry point
│       ├── static/        # Web interface files
│       ├── ml/            # Machine learning components
│       └── scoring/       # Scoring algorithms
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── examples/              # Sample files
├── tests/                 # Test files
├── infra/                 # Infrastructure (Docker)
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project configuration
└── README.md             # This file
```

## Features

- **Multi-format Support**: PDF, DOCX, and image files (with OCR)
- **AI-Powered Parsing**: Uses GPT-4o-mini for intelligent text extraction
- **Canonical JSON Output**: Standardized resume and job description format
- **MongoDB Storage**: Persistent storage with deduplication
- **Embedding Generation**: Vector embeddings for semantic matching
- **Scoring System**: Rule-based and semantic candidate-job matching
- **Web Interface**: Modern drag-and-drop upload interface
- **Mock Mode**: Development mode with deterministic outputs

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export OPENAI_API_KEY="your-openai-api-key"
export MONGODB_URI="mongodb://localhost:27017"
export DB_NAME="hyperrecruit"
export HRP_USE_MOCK="false"
```

### 3. Start MongoDB
```bash
docker compose -f infra/docker-compose.yml up -d
```

### 4. Run the Application
```bash
# Using the run script
./run.sh

# Or directly with uvicorn
uvicorn src.app.main:app --reload --port 8080
```

### 5. Access the Web Interface
Open your browser and go to: http://localhost:8080

## API Endpoints

### Resume Parsing
- `POST /hr/parser/single` - Parse a single resume
- `POST /hr/parser/bulk` - Parse multiple resumes

### Job Description Parsing
- `POST /hr/jobs/single` - Parse a single job description
- `POST /hr/jobs/bulk` - Parse multiple job descriptions

### Scoring
- `POST /hr/scoring/candidate/{candidate_id}` - Score candidate against all jobs
- `POST /hr/scoring/job/{job_id}` - Score job against all candidates
- `GET /hr/scoring/candidate/{candidate_id}/job/{job_id}` - Get specific match score

## Development

### Install in Development Mode
```bash
pip install -e .
```

### Run Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
isort src/
```

## Configuration

The application uses environment variables for configuration:

- `OPENAI_API_KEY` - Your OpenAI API key
- `MONGODB_URI` - MongoDB connection string (default: mongodb://localhost:27017)
- `DB_NAME` - Database name (default: hyperrecruit)
- `HRP_USE_MOCK` - Enable mock mode for development (default: false)
- `HRP_MAX_INPUT_CHARS` - Maximum input characters (default: 180000)
- `HRP_MAX_OUTPUT_TOKENS` - Maximum output tokens (default: 3000)

## License

MIT License