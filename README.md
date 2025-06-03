# Quickcart E-commerce Platform

## Overview

Quickcart is a modular, scalable e-commerce platform designed to handle complex inventory management, multi-warehouse operations, and flexible product configurations. The system consists of several interconnected components:

- **EMS (E-commerce Management System)** - Core shopping experience, catalog, and checkout
- **PMS (Product Management System)** - Product information management
- **Common** - Shred core services and utilities

The platform supports advanced inventory features including preorders, backorders, multi-warehouse stock management, and reservations.

## System Requirements

### Development Environment

- Python 3.12+
- Node.js 16+ (for frontend assets)
- PostgreSQL 14+ (production) or SQLite (development)
- Redis (for caching and task queues)

### Dependencies

- Django 4.2+
- Django REST Framework
- Celery (for async task processing)
- TailwindCSS (for styling)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/Quickcart.git
cd Quickcart_master
```

### 2. Set up a virtual environment

```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
npm install
```

### 5. Configure environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` to configure database connection, secret key, and other settings.

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Run the development server

```bash
python manage.py runserver
```

Access the admin interface at http://localhost:8000/admin/

## Project Structure

The project is organized into several main directories:

- `ems/` - E-commerce Management System
  - `djangoapps/` - Django applications for EMS functionality
    - `product/` - Product catalog and management
    - `warehouse/` - Inventory and warehouse management
    - `order/` - Order processing
    - `checkout/` - Checkout process
    - `account/` - User accounts and authentication
    - Other specialized modules
  - `envs/` - Environment-specific settings
  - `static/` - Static assets for EMS
  - `templates/` - HTML templates

- `pms/` - Product Management System
  - `djangoapps/` - Django applications for PMS functionality
    - `product/` - Product information management
    - `order/` - Order management

- `quickcart/` - Shared core services
  - `core/` - Core functionality shared across all systems
    - `djangoapps/` - Django applications for core functionality
    - `djangolib/` - Django libraries
    - `lib/` - General purpose libraries

- `common/` - Common code shared between systems
  - `djangoapps/` - Django applications for common functionality
    - `customer/` - Customer information
    - `util/` - Utility functions

- `static/` - Collected static files
- `templates/` - Global templates
- `logs/` - Application logs

## Development Setup

### Setting up a development environment

1. Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

2. Set up pre-commit hooks:

```bash
pre-commit install
```

3. Build frontend assets during development:

```bash
npm run dev
```

4. Run tests:

```bash
pytest
```

### Development workflow

1. Create a feature branch from `main`:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes, following the coding standards

3. Write tests for your changes

4. Run the test suite:

```bash
pytest
```

5. Submit a pull request to the `main` branch

## Contributing

### Coding Standards

- Follow PEP 8 for Python code
- Write docstrings for all classes and functions
- Follow Django's style guide for Django-specific code
- Use type hints where appropriate

### Testing

- Write unit tests for all new functionality
- Ensure tests pass before submitting pull requests
- Aim for high test coverage

### Pull Request Process

1. Update the README.md or documentation with details of changes if appropriate
2. Update the version number in relevant files following Semantic Versioning
3. The PR must pass all automated tests
4. The PR must be reviewed by at least one maintainer before merging

## License

This project is licensed under the [MIT License](LICENSE).

