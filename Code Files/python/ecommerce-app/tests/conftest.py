"""Shared pytest configuration for the e-commerce app tests."""

import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def pytest_configure(config):
    config.addinivalue_line("markers", "apple_pay: marks Apple Pay payment flow tests")
    config.addinivalue_line("markers", "pci_dss: marks PCI DSS log-sanitisation tests")
    config.addinivalue_line("markers", "retry: marks retry behaviour tests")
    config.addinivalue_line("markers", "rollback: marks rollback tests")


@pytest.fixture(autouse=True)
def reset_logging(caplog):
    caplog.clear()
    yield
