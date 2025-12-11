from playwright.sync_api import sync_playwright

def verify_login_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to Login Page
        page.goto("http://localhost:5173/login")

        # Wait for key elements to ensure render
        page.wait_for_selector(".auth-card")
        page.wait_for_selector("input[type='email']")
        page.wait_for_selector("input[type='password']")
        page.wait_for_selector("button[type='submit']")

        # Fill inputs to verify interactivity
        page.fill("input[type='email']", "test@example.com")
        page.fill("input[type='password']", "password123")

        # Screenshot the login page
        page.screenshot(path="verification/login_page.png", full_page=True)
        browser.close()

if __name__ == "__main__":
    verify_login_page()
