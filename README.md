# DocumentScrapper

DocumentScrapper is a Python-based application for searching, downloading, validating, and processing various document types from the web. It provides a comprehensive API for document operations with support for parallel downloads, structured logging, and detailed report generation.

## Features

- Search and download documents (PDF, DOCX, XLSX, images) from the web using FireCrawl API
- Validate and process downloaded documents with configurable validation rules
- Structured logging with JSON support for easier monitoring and debugging
- Generate detailed reports in Excel or text format
- RESTful API built with FastAPI for seamless integration
- Parallel downloads for improved efficiency and performance
- Configurable document classes and search queries to match your needs

## Project Structure

```
DocumentScrapper/
├── agents/                # Document search and download agents
│   └── doc_agent.py
├── api/                   # FastAPI application and middleware
│   ├── main.py
│   └── middleware.py
├── config/                # Document class configuration
│   └── document_classes.py
├── crawlers/              # Web crawling clients (FireCrawl)
│   └── firecrawl_client.py
├── tests/                 # Unit and integration tests
│   └── test_api.py
├── utils/                 # Utilities: logging, downloading, validation, reporting
│   ├── document_processor.py
│   ├── downloader.py
│   ├── file_validator.py
│   ├── logger.py
│   ├── parallel_downloader.py
│   ├── report_generator.py
│   └── __init__.py
├── .env                   # Environment variables (API keys, etc.)
├── .gitignore
├── main.py                # Entry point for CLI operations
├── pyproject.toml         # Poetry configuration
└── README.md              # Project documentation
```

## Core Modules

### Document Agent (`agents/doc_agent.py`)
The central component responsible for orchestrating document search operations and managing the download workflow. It coordinates between search queries, the FireCrawl client, and document processors.

### API Layer (`api/main.py`, `api/middleware.py`)
A FastAPI implementation providing RESTful endpoints for all document operations. Features include:
- Document class management
- Search and download orchestration
- Report generation and retrieval
- Authentication and rate limiting via middleware

### Document Configuration (`config/document_classes.py`)
Defines all supported document types with their respective search parameters, validation rules, and processing instructions. Document classes are fully configurable to match different use cases.

### FireCrawl Integration (`crawlers/firecrawl_client.py`)
Handles communication with the FireCrawl API for efficient web searching and document discovery. Includes robust error handling and retry mechanisms.

### Utility Modules (`utils/`)
- `document_processor.py`: Processes and extracts information from downloaded documents
- `downloader.py`: Manages file downloads from identified URLs
- `file_validator.py`: Validates downloaded files for integrity and content quality
- `logger.py`: Configurable logging with JSON support and rotation policies
- `parallel_downloader.py`: Implements concurrent download capabilities
- `report_generator.py`: Creates detailed reports in various formats

## Getting Started

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/) for dependency management
- FireCrawl API account and key

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd DocumentScrapper
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env` and fill in required values:
     ```
     FIRECRAWL_API_KEY=your_firecrawl_api_key
     LOG_LEVEL=INFO
     MAX_PARALLEL_DOWNLOADS=5
     ```

### Development Environment Setup

1. **Install development dependencies:**
   ```bash
   poetry install --with dev
   ```

2. **Set up pre-commit hooks:**
   ```bash
   poetry run pre-commit install
   ```

3. **Configure IDE:**
   - Recommended VSCode extensions:
     - Python
     - Pylance
     - Black formatter
     - isort

## Running the Application

### Starting the API Server

```bash
poetry run uvicorn api.main:app --reload --port 8000
```

- The API will be available at http://localhost:8000
- Interactive API documentation: http://localhost:8000/docs
- Alternative OpenAPI docs: http://localhost:8000/redoc

### Using the CLI Interface

```bash
# List available document classes
poetry run python main.py list-classes

# Search and download documents
poetry run python main.py search --class-id company_annual_reports --limit 10

# Generate a report
poetry run python main.py generate-report --format excel
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/document/classes` | GET | List all available document classes |
| `/search` | POST | Search and download documents by class |
| `/report` | GET | Generate reports of downloaded documents |
| `/status` | GET | Get system status and statistics |

See the API documentation at `/docs` for detailed request/response schemas and examples.

## Configuration Options

### Document Classes

Document classes are defined in `config/document_classes.py` and can be customized to support different document types, search queries, and validation rules:

```python
DOCUMENT_CLASSES = {
    "company_annual_reports": {
        "description": "Annual financial reports for public companies",
        "search_patterns": ["annual report", "10-K", "financial statement"],
        "file_types": ["pdf", "docx"],
        "validators": ["size_check", "keyword_check", "structure_check"],
        "keywords": ["revenue", "profit", "balance sheet"]
    },
    # Add more document classes as needed
}
```

### Logging Configuration

Logs are stored in the `logs/` directory with the following default settings:
- JSON structured format for machine parsing
- Daily rotation with 30-day retention
- Configurable log levels via environment variables

Customize logging behavior in `utils/logger.py`.

### Storage Configuration

- Downloaded documents: `data/raw_docs/{document_class}/{date}/`
- Processed data: `data/processed/{document_class}/`
- Reports: `data/reports/{report_type}/{date}.{format}`

## Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test modules
poetry run pytest tests/test_api.py

# Run with coverage report
poetry run pytest --cov=. --cov-report=html
```

### Writing Tests

- Unit tests: Write tests for individual functions and classes
- Integration tests: Test API endpoints and document workflows
- Mock external services like FireCrawl API using `unittest.mock` or `pytest-mock`

Example test structure in `tests/test_api.py`:

```python
def test_search_endpoint():
    # Test setup, API call, and assertions
```

## Troubleshooting

Common issues and solutions:

1. **API Connection Errors**: Check your FireCrawl API key and network connectivity
2. **Download Failures**: Verify target URLs are accessible and not rate-limited
3. **Processing Errors**: Ensure document formats match expected types and structures

See logs for detailed error information.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Run tests: `poetry run pytest`
5. Commit: `git commit -m "Add awesome feature"`
6. Push: `git push origin feature/my-feature`
7. Create a pull request

Please follow the coding standards and include tests for new features.

## License

MIT License

---

**Note**: This project is for educational and research purposes. Ensure compliance with all applicable laws and terms of service when scraping or downloading documents from the web.
