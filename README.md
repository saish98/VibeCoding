# Tax Advisor API - Phase 1: Database Setup

## Overview
This repository contains the Phase 1 implementation of the Tax Advisor API, focusing on database setup and connection management. The system uses SQLite for local development with a hybrid database approach that can be extended to PostgreSQL for production.

## Project Structure
```
.
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py       # Database connection management
│   │   ├── models.py           # Data models and schemas
│   │   ├── utils.py            # Database utilities and operations
│   │   └── migrations.py       # Database migration system
│   └── config/
│       ├── __init__.py
│       └── settings.py         # Configuration management
├── requirements.txt            # Python dependencies
├── test_database.py           # Database testing script
├── local_database.db          # SQLite database (created on first run)
├── uploads/                   # File upload directory (created automatically)
└── README.md                  # This file
```

## Database Schema

### Core Tables

1. **user_sessions** - Manages user session data
   - `session_id` (TEXT, PRIMARY KEY)
   - `created_at` (TIMESTAMP)
   - `expires_at` (TIMESTAMP)

2. **documents** - Stores uploaded PDF document metadata
   - `id` (INTEGER, PRIMARY KEY)
   - `session_id` (TEXT, FOREIGN KEY)
   - `file_name` (TEXT)
   - `file_url` (TEXT)
   - `file_type` (TEXT)
   - `upload_timestamp` (TIMESTAMP)

3. **user_inputs** - Stores manual data input from users
   - `id` (INTEGER, PRIMARY KEY)
   - `session_id` (TEXT, FOREIGN KEY)
   - `input_type` (TEXT)
   - `field_name` (TEXT)
   - `field_value` (TEXT)
   - `timestamp` (TIMESTAMP)

4. **tax_calculations** - Stores calculated tax results
   - `id` (INTEGER, PRIMARY KEY)
   - `session_id` (TEXT, FOREIGN KEY)
   - `gross_income` (REAL)
   - `tax_old_regime` (REAL)
   - `tax_new_regime` (REAL)
   - `total_deductions` (REAL)
   - `net_tax` (REAL)
   - `calculation_timestamp` (TIMESTAMP)

5. **ai_conversations** - Stores AI chat conversation history
   - `id` (INTEGER, PRIMARY KEY)
   - `session_id` (TEXT, FOREIGN KEY)
   - `user_message` (TEXT)
   - `ai_response` (TEXT)
   - `timestamp` (TIMESTAMP)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or navigate to the project directory**
   ```bash
   cd /path/to/your/project
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the database test**
   ```bash
   python test_database.py
   ```

4. **Start the API server** (optional)
   ```bash
   python -m api.main
   ```

## Configuration

### Environment Variables
Create a `.env.local` file in the project root with the following variables:

```env
# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./local_database.db

# Application Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
SESSION_TIMEOUT_HOURS=24

# File Storage
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=10485760

# Gemini API (for later phases)
GEMINI_API_KEY=your-gemini-api-key
```

## Usage

### Database Operations

```python
from api.database.connection import DatabaseManager
from api.database.utils import DatabaseUtils

# Initialize database
db_manager = DatabaseManager()
utils = DatabaseUtils(db_manager)

# Create a new session
session_id = utils.create_session()

# Save document metadata
doc_id = utils.save_document(
    session_id=session_id,
    file_name="payslip.pdf",
    file_url="/uploads/payslip.pdf",
    file_type="payslip"
)

# Save user input
input_id = utils.save_user_input(
    session_id=session_id,
    input_type="salary",
    field_name="basic_salary",
    field_value="500000"
)

# Save tax calculation
calc_id = utils.save_tax_calculation(
    session_id=session_id,
    gross_income=500000.0,
    tax_old_regime=25000.0,
    tax_new_regime=30000.0,
    total_deductions=50000.0,
    net_tax=25000.0
)

# Get session data
session_data = utils.get_session_data(session_id)
```

### Migration System

```python
from api.database.migrations import DatabaseMigration

# Run migrations
migration = DatabaseMigration()
migration.run_migrations()
```

## Testing

### Run All Tests
```bash
python test_database.py
```

### Test Results
The test script validates:
- ✅ Database connection and table creation
- ✅ Session management (create, validate, cleanup)
- ✅ CRUD operations for all tables
- ✅ Migration system functionality
- ✅ Configuration management

## API Endpoints

When running the FastAPI server, the following endpoints are available:

- `GET /` - Health check
- `GET /health` - Detailed health check
- `GET /docs` - API documentation (Swagger UI)

## Development

### Adding New Tables
1. Add table creation SQL to `DatabaseManager.create_tables()`
2. Create corresponding model in `models.py`
3. Add utility methods in `DatabaseUtils`
4. Create migration in `migrations.py`
5. Update tests in `test_database.py`

### Database Migrations
The migration system tracks schema changes and ensures consistent database state across environments.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory
2. **Database Lock**: Close any open database connections or restart the application
3. **Permission Errors**: Ensure write permissions for the project directory

### Debug Mode
Set `DEBUG=True` in your environment variables for detailed error messages.

## Next Steps

Phase 1 completion enables:
- **Phase 2**: PDF upload system
- **Phase 3**: User input forms
- **Phase 4**: Tax calculations
- **Phase 5**: AI integration
- **Phase 6**: Chat system
- **Phase 7**: Complete application

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

This project is part of the Tax Advisor API development. 