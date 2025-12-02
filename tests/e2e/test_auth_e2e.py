import pytest
import time


@pytest.mark.e2e
def test_register_and_login_positive(page, fastapi_server):
    # use timestamped username/email to avoid duplicates
    ts = str(int(time.time() * 1000))[-6:]
    username = f'user{ts}'
    email = f'{username}@example.com'
    password = 'password123'

    # Go to register page
    page.goto('http://localhost:8000/register')
    page.fill('#email', email)
    page.fill('#username', username)
    page.fill('#password', password)
    page.fill('#confirm', password)
    page.click('button:text("Register")')
    # wait for message to contain text
    page.wait_for_function('document.querySelector("#message").innerText.length > 0')
    assert 'Registration successful' in page.inner_text('#message')

    # token should be stored
    token = page.evaluate('window.localStorage.getItem("access_token")')
    assert token is not None and len(token) > 0

    # Now log out locally then login via login page
    page.evaluate('window.localStorage.removeItem("access_token")')
    page.goto('http://localhost:8000/login')
    page.fill('#username', username)
    page.fill('#password', password)
    page.click('button:text("Login")')
    # wait for message to contain text
    page.wait_for_function('document.querySelector("#message").innerText.length > 0')
    assert 'Login successful' in page.inner_text('#message')
    token2 = page.evaluate('window.localStorage.getItem("access_token")')
    assert token2 is not None and len(token2) > 0


@pytest.mark.e2e
def test_register_short_password_shows_error(page, fastapi_server):
    page.goto('http://localhost:8000/register')
    page.fill('#email', 'shortpass@example.com')
    page.fill('#username', 'shortpass')
    page.fill('#password', '123')
    page.fill('#confirm', '123')
    page.click('button:text("Register")')
    page.wait_for_function('document.querySelector("#message").innerText.length > 0')
    assert 'Password must be at least 6 characters' in page.inner_text('#message')


@pytest.mark.e2e
def test_login_wrong_password_shows_error(page, fastapi_server):
    # attempt to login with invalid credentials
    page.goto('http://localhost:8000/login')
    page.fill('#username', 'nonexist')
    page.fill('#password', 'wrongpassword')
    page.click('button:text("Login")')
    page.wait_for_function('document.querySelector("#message").innerText.length > 0')
    # server returns 401 and JS will show message text
    assert 'Invalid credentials' in page.inner_text('#message') or 'Login failed' in page.inner_text('#message')
