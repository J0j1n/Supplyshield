# SupplyShield

A comprehensive software supply chain security platform to analyze dependencies and identify vulnerabilities.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.0-green)

*This is a final-year B.Tech Cyber Security major project.*

## Features

**Phase 1**
- Automated dependency scanning and identification
- Vulnerability detection via multiple sources (OSV, NVD)
- SBOM (Software Bill of Materials) generation

**Phase 2**
- Advanced Trust Scoring for dependencies
- Trust Level categorization
- Enhanced reporting and dashboard analytics

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/supplyshield.git
cd supplyshield

# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the Flask development server
flask run
```

## Architecture

SupplyShield is built as a modular monolith, emphasizing clear separation of concerns between domains such as scanning, reporting, and database storage.

## Project Structure

```
supplyshield/
├── app/                  # Main application package
│   ├── core/             # Core scanning logic and domain managers
│   ├── models/           # SQLAlchemy database models
│   ├── __init__.py       # App factory
│   └── extensions.py     # Flask extensions setup
├── instance/             # Local database and instance-specific configs
├── logs/                 # Application log files
├── uploads/              # Temporary upload directory for source code
├── workspaces/           # Isolated environments for scanning
├── config.py             # Configuration classes
├── requirements.txt      # Project dependencies
├── run.py                # Application entry point
└── README.md             # Project documentation
```

## Tech Stack

| Component         | Technology                  |
|-------------------|-----------------------------|
| **Backend**       | Python 3, Flask             |
| **Database**      | SQLite (Dev), SQLAlchemy ORM|
| **Vulnerability** | OSV API, NVD Data           |

## Design Principles
- Separation of Concerns
- Secure by Default
- Scalable Architecture
- Easily Extensible

## License

This project is licensed under the MIT License - see the LICENSE file for details.
