# Testing Documentation

This directory contains documentation related to testing the Chelal Hospital Management System.

## Contents

- [Testing Strategy](testing-strategy.md) - Overall testing approach and methodology
- [Unit Testing](unit-testing.md) - Guide to writing and running unit tests
- [Integration Testing](integration-testing.md) - API and integration test documentation
- [End-to-End Testing](e2e-testing.md) - Complete workflow testing
- [Test Data Management](test-data.md) - Managing test fixtures and data
- [Performance Testing](performance-testing.md) - Load and performance testing
- [Security Testing](security-testing.md) - Security vulnerability testing

## Quick Test Commands

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core

# Run with coverage
coverage run --source='.' manage.py test
coverage report

# Run specific test class
python manage.py test core.tests.PatientAPITest

# Run with verbose output
python manage.py test --verbosity=2
```

## Test Environment Setup

```bash
# Install test dependencies
pip install pytest pytest-django coverage factory-boy

# Set up test database
export DATABASE_URL=postgresql://test_user:test_pass@localhost/test_chelal_hms

# Run tests
pytest
```

For detailed testing information, see the individual documentation files in this directory.