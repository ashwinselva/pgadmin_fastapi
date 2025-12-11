import pytest
import uuid


@pytest.mark.e2e
def test_profile_change_password_flow(page, fastapi_server):
    # Use a unique username/email to avoid conflicts with persistent DB
    unique = uuid.uuid4().hex[:8]
    username = f"e2euser_{unique}"
    email = f"{username}@example.com"

    # Register a new user via the UI
    page.goto('http://localhost:8000/register')
    page.fill('#username', username)
    page.fill('#email', email)
    page.fill('#password', 'startpass')
    page.fill('#confirm', 'startpass')
    page.click('button:text("Register")')
    # after registration, redirect to login
    page.wait_for_url('**/login')

    # Login
    page.fill('#username', username)
    page.fill('#password', 'startpass')
    page.click('button:text("Login")')
    page.wait_for_url('**/')

    # Go to profile page
    page.goto('http://localhost:8000/profile')
    page.wait_for_selector('#old_password')

    # Change password
    page.fill('#old_password', 'startpass')
    page.fill('#new_password', 'newpass123')
    page.click('button:text("Change Password")')

    # Should redirect to login after change
    page.wait_for_url('**/login')

    # Login with new password programmatically (avoid intermittent UI click issues)
    login_js = f'''async () => {{
        const res = await fetch('/users/login', {{
            method: 'POST', headers: {{'Content-Type':'application/json'}},
            body: JSON.stringify({{username: '{username}', password: 'newpass123'}})
        }});
        const data = await res.json();
        if (data.access_token) localStorage.setItem('access_token', data.access_token);
        return res.status;
    }}'''
    status = page.evaluate(login_js)
    assert status == 200
    page.goto('http://localhost:8000/')
    page.wait_for_selector('h1')
    assert page.query_selector('h1') is not None
