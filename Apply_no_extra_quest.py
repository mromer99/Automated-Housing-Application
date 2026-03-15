import time
import json
import random

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Constants / locators ---

GECKODRIVER_PATH = "/snap/bin/geckodriver"

COOKIE_BUTTON_XPATH = "//button[contains(text(),'Speichern wie ausgewählt')]"
COOKIE_LINK_XPATH = "//a[contains(text(),'Speichern wie ausgewählt')]"
ERROR_ELEMENT_XPATH = "//div[contains(@class, 'ant-alert-error')]//span[contains(text(), 'Fehler beim Laden')]"
ANFRAGE_SENDEN_XPATH = "(//button[contains(text(), 'Anfrage senden')])[1]"
CLICK_SCRIPT = "arguments[0].click();"

TYPING_DELAY = 0.02  # fast but not instant

# --- Small helpers ---


def random_delay(min_sec=0.2, max_sec=0.6):
    time.sleep(random.uniform(min_sec, max_sec))


def type_like_human(element, text: str):
    """Fast but slightly irregular typing, mostly for stability/UX."""
    text = str(text).strip()
    for ch in text:
        element.send_keys(ch)
        # small jitter around base delay
        time.sleep(max(0.005, TYPING_DELAY + random.uniform(-0.005, 0.01)))


def human_click(driver, element):
    """Scroll to element and click it with ActionChains."""
    driver.execute_script(
        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element
    )
    time.sleep(0.2)
    actions = ActionChains(driver)
    actions.move_to_element(element).pause(random.uniform(0.05, 0.15)).click().perform()
    time.sleep(0.2)


# --- Webdriver / cookies ---


def create_firefox_driver():
    options = Options()
    # visible browser (easier to debug). Add -headless if you need.
    # options.add_argument("-headless")

    service = Service(executable_path=GECKODRIVER_PATH)
    driver = webdriver.Firefox(service=service, options=options)
    driver.maximize_window()
    return driver


def accept_cookies(driver, timeout=10):
    wait = WebDriverWait(driver, timeout)
    try:
        random_delay(0.2, 0.6)
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, COOKIE_BUTTON_XPATH)))
        human_click(driver, btn)
        return True
    except Exception:
        try:
            link = wait.until(EC.element_to_be_clickable((By.XPATH, COOKIE_LINK_XPATH)))
            human_click(driver, link)
            return True
        except Exception:
            print("No cookie prompt found / already accepted.")
            return False


def refresh_page_and_retry(driver, wait):
    print("Refreshing page...")
    driver.refresh()
    time.sleep(2)
    accept_cookies(driver)
    anfrage_senden = wait.until(
        EC.element_to_be_clickable((By.XPATH, ANFRAGE_SENDEN_XPATH))
    )
    driver.execute_script(CLICK_SCRIPT, anfrage_senden)
    time.sleep(1.5)


# --- Data loading / CLI ---


def load_user_details(num_people):
    filename = f"user_details_{num_people}.json"
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        print(f"Loaded user details from {filename} ({len(data)} user(s))")
        return data
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


def get_user_input():
    print("=" * 50)
    print("Home Application Automation Tool")
    print("=" * 50)
    link = input("Please enter the application link: ").strip()
    if not link:
        print("No link provided.")
        return None, None

    if not link.startswith(("http://", "https://")):
        link = "https://" + link

    while True:
        n = input("How many people (1, 2, or 3): ").strip()
        if n in {"1", "2", "3"}:
            return link, int(n)
        print("Please enter 1, 2, or 3.")


# --- Core form logic ---


def fill_form(driver, wait, details):
    print(f"Starting form filling for {details['first_name']} {details['surname']}")

    # 1) Click "Anfrage senden" (with retry if loading error)
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Clicking 'Anfrage senden' (attempt {attempt})")
            anfrage_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, ANFRAGE_SENDEN_XPATH))
            )
            driver.execute_script(CLICK_SCRIPT, anfrage_btn)
            time.sleep(1.5)

            # check for "Fehler beim Laden"
            try:
                err = driver.find_element(By.XPATH, ERROR_ELEMENT_XPATH)
                if err:
                    print("Fehler beim Laden detected – refreshing...")
                    refresh_page_and_retry(driver, wait)
            except Exception:
                pass
            break
        except Exception as e:
            print(f"Error clicking 'Anfrage senden': {e}")
            if attempt == max_retries:
                raise

    # 2) Switch to iframe
    print("Switching to iframe...")
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "contact-iframe")))
    time.sleep(0.5)

    # 3) Select Anrede = Herr
    print("Selecting 'Herr'...")
    try:
        dropdown_container = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "ng-select-container"))
        )
        human_click(driver, dropdown_container)
        time.sleep(0.4)
        herr_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Herr')]"))
        )
        human_click(driver, herr_option)
    except Exception as e:
        print(f"Could not select 'Herr': {e}")

    # 4) Personal data
    # First name
    try:
        first_name_input = wait.until(
            EC.presence_of_element_located((By.ID, "firstName"))
        )
    except Exception:
        first_name_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//input[@formcontrolname="firstName"]')
            )
        )
    first_name_input.clear()
    type_like_human(first_name_input, details["first_name"])

    # Last name
    try:
        surname_input = wait.until(
            EC.presence_of_element_located((By.ID, "lastName"))
        )
    except Exception:
        surname_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//input[@formcontrolname="lastName"]')
            )
        )
    surname_input.clear()
    type_like_human(surname_input, details["surname"])

    # Email
    email_input = wait.until(
        EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="email"]'))
    )
    email_input.clear()
    type_like_human(email_input, details["email"])

    # Street
    try:
        street_input = wait.until(
            EC.presence_of_element_located((By.ID, "street"))
        )
    except Exception:
        street_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//input[@formcontrolname="street"]')
            )
        )
    street_input.clear()
    type_like_human(street_input, details["street"])

    # House number
    house_number_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//input[@formcontrolname="houseNumber"]')
        )
    )
    house_number_input.clear()
    type_like_human(house_number_input, details["house_number"])

    # Postal code
    zip_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//input[@formcontrolname="zipCode"]')
        )
    )
    zip_input.clear()
    type_like_human(zip_input, details["postal_code"])

    # City
    city_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//input[@formcontrolname="city"]')
        )
    )
    city_input.clear()
    type_like_human(city_input, details["city"])

    # Total persons
    total_input = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//input[@data-cy='formly_2_input_gewobag_gesamtzahl_der_einziehenden_personen_erwachsene_und_kinder_0']",
            )
        )
    )
    total_input.clear()
    type_like_human(total_input, details["total_persons"])

    # Phone number
    try:
        phone_input = wait.until(
            EC.presence_of_element_located(
                (By.ID, "formly_17_input_$$_telephone_number_$$_0")
            )
        )
    except Exception:
        phone_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//input[@formcontrolname="phoneNumber"]')
            )
        )
    phone_input.clear()
    type_like_human(phone_input, details["phone_number"])

    # 5) Application type: "Für mich selbst"
    print("Selecting 'Für mich selbst'...")
    try:
        dropdown = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//ng-select[contains(@id,'fuer_wen_wird_die_wohnungsanfrage_gestellt')]",
                )
            )
        )
        human_click(driver, dropdown)
        time.sleep(0.4)
        option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(),'Für mich selbst')]")
            )
        )
        human_click(driver, option)
    except Exception as e:
        print(f"Could not select application type: {e}")

    # 6) Privacy checkbox
    print("Accepting privacy policy...")
    try:
        checkbox = wait.until(
            EC.element_to_be_clickable(
                (By.ID, "formly_20_checkbox_gewobag_datenschutzhinweis_bestaetigt_0")
            )
        )
        human_click(driver, checkbox)
    except Exception as e:
        print(f"Could not click privacy checkbox: {e}")

    # 7) Submit
    print("Submitting application...")
    try:
        submit_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-cy='btn-submit']"))
        )
    except Exception:
        submit_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(text(),'Anfrage versenden') or @type='submit']",
                )
            )
        )
        
    time.sleep(2)

    human_click(driver, submit_btn)
    time.sleep(2.0)


# --- Main ---


def main():
    link, num_people = get_user_input()
    if not link:
        return 1

    users = load_user_details(num_people)
    if not users:
        return 1

    for i, user in enumerate(users, start=1):
        print(f"\n{'='*50}")
        print(f"Processing user {i}/{len(users)}")
        print(f"{user['first_name']} {user['surname']} – {user['email']}")
        print(f"{'='*50}\n")

        driver = create_firefox_driver()
        wait = WebDriverWait(driver, 15)

        try:
            print(f"Opening: {link}")
            driver.get(link)
            time.sleep(2)
            accept_cookies(driver, 15)
            fill_form(driver, wait, user)
            print(f"✓ Form submitted for {user['email']}")
        finally:
            driver.quit()

        if i < len(users):
            pause = random.uniform(1.0, 2.0)
            print(f"Waiting {pause:.1f}s before next user...")
            time.sleep(2)

    print("\n✓ All applications completed!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
