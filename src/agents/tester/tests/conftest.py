import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: marks tests that call external APIs (deselect with -m 'not integration')",
    )
