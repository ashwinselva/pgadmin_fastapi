# tests/e2e/test_e2e.py

import pytest  # Import the pytest framework for writing and running tests

# The following decorators and functions define E2E tests for the FastAPI calculator application.

@pytest.mark.e2e
def test_hello_world(page, fastapi_server):
    """
    Test that the homepage displays the calculator page.

    This test verifies that when a user navigates to the homepage of the application,
    the main header displays "Advanced Calculator". This ensures that the server is running
    and serving the correct template.
    """
    page.goto('http://localhost:8000')
    assert page.inner_text('h1') == 'Advanced Calculator'

@pytest.mark.e2e
def test_calculator_add(page, fastapi_server):
    """
    Test the addition functionality of the calculator.

    This test fills in two numbers, clicks the "Add" button, and verifies
    that the result displayed contains the correct result value.
    """
    page.goto('http://localhost:8000')
    page.fill('#a', '10')
    page.fill('#b', '5')
    page.click('button:text("➕ Add")')
    page.wait_for_function('document.querySelector("#result").innerText.includes("✅")')
    assert '15' in page.inner_text('#result')

@pytest.mark.e2e
def test_calculator_divide_by_zero(page, fastapi_server):
    """
    Test the divide by zero functionality of the calculator.

    This test fills in numbers, clicks the "Divide" button, and verifies that the appropriate
    error message is displayed.
    """
    page.goto('http://localhost:8000')
    page.fill('#a', '10')
    page.fill('#b', '0')
    page.click('button:text("➗ Divide")')
    page.wait_for_function('document.querySelector("#result").innerText.includes("❌")')
    result_text = page.inner_text('#result').lower()
    assert 'error' in result_text or 'failed' in result_text
