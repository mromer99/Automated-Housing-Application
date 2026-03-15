import time
import json
import logging
import random

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Logging ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# --- Constants / locators ---

GECKODRIVER_PATH = "/snap/bin/geckodriver"

COOKIE_BUTTON_XPATH = "//button[contains(text(),'Speichern wie ausgewählt')]"
COOKIE_LINK_XPATH = "//a[contains(text(),'Speichern wie ausgewählt')]"
ERROR_ELEMENT_XPATH = (
    "//div[contains(@class, 'ant-alert-error')]"
    "//span[contains(text(), 'Fehler beim Laden')]"
)
ANFRAGE_SENDEN_XPATH = "(//button[contains(text(), 'Anfrage senden')])[1]"
CLICK_SCRIPT = "arguments[0].click();"

TYPING_DELAY = 0.01  # faster than before (was 0.02)

REQUIRED_FIELDS = [
    "email", "first_name", "surname", "phone_number",
    "street", "house_number", "postal_code", "city", "total_persons",
]


# --- Small helpers ---


def random_delay(min_sec=0.2, max_sec=0.6):
    time.sleep(random.uniform(min_sec, max_sec))


def type_like_human(element, text: str):
    """Fast but slightly irregular typing, mostly for stability/UX."""
    text = str(text).strip()
    element.clear()
    for ch in text:
        element.send_keys(ch)
        time.sleep(max(0.005, TYPING_DELAY + random.uniform(-0.005, 0.01)))


def human_click(driver, element):
    """Scroll element into view and click it with ActionChains."""
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element,
        )
        time.sleep(0.15)
    except Exception:
        pass

    actions = ActionChains(driver)
    actions.move_to_element(element).pause(
        random.uniform(0.05, 0.15)
    ).click().perform()
    time.sleep(0.15)


def find_element_with_fallback(wait, primary, fallback):
    """Try primary locator, fall back to secondary."""
    try:
        return wait.until(EC.presence_of_element_located(primary))
    except Exception:
        return wait.until(EC.presence_of_element_located(fallback))


def safe_fill_field(wait, locator, value, field_name="field"):
    """Try to find and fill a field; log and skip if not found."""
    try:
        element = wait.until(EC.presence_of_element_located(locator))
        type_like_human(element, value)
        return True
    except Exception:
        log.info(f"  - {field_name} not found, skipping.")
        return False


# --- Webdriver / cookies ---


def create_firefox_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless")

    # Anti-detection preferences
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    options.set_preference(
        "general.useragent.override",
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
    )
    options.set_preference("privacy.trackingprotection.enabled", False)

    service = Service(executable_path=GECKODRIVER_PATH)
    driver = webdriver.Firefox(service=service, options=options)

    # Runtime anti-detection
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'languages', {
            get: () => ['de-DE', 'de', 'en-US', 'en']
        });
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)

    driver.maximize_window()
    log.info("Firefox initialized with anti-detection measures")
    return driver


def accept_cookies(driver, timeout=5):
    wait = WebDriverWait(driver, timeout)
    try:
        random_delay(0.2, 0.6)
        btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, COOKIE_BUTTON_XPATH))
        )
        human_click(driver, btn)
        return True
    except Exception:
        try:
            link = wait.until(
                EC.element_to_be_clickable((By.XPATH, COOKIE_LINK_XPATH))
            )
            human_click(driver, link)
            return True
        except Exception:
            log.info("No cookie prompt found / could not click it.")
            return False


def refresh_page_and_retry(driver, wait, attempt=1):
    """Check for 'Fehler beim Laden' error, refresh with backoff if found."""
    try:
        error_element = wait.until(
            EC.presence_of_element_located((By.XPATH, ERROR_ELEMENT_XPATH))
        )
        if error_element:
            backoff = min(1.5 * (2 ** (attempt - 1)), 8)
            log.warning(
                f"Detected 'Fehler beim Laden'. Waiting {backoff:.1f}s, then refreshing..."
            )
            time.sleep(backoff)
            driver.refresh()
            time.sleep(1.0)
            return True
    except Exception:
        pass
    return False


# --- Core form logic ---


def fill_form(driver, wait, details, wbs_mode=True):
    log.info(f"Starting form filling for {details['first_name']} {details['surname']}")

    # 1) Click "Anfrage senden" (with retry if loading error)
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            log.info(f"Clicking 'Anfrage senden' (attempt {attempt})")
            anfrage_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, ANFRAGE_SENDEN_XPATH))
            )
            driver.execute_script(CLICK_SCRIPT, anfrage_btn)
            time.sleep(1.0)

            if refresh_page_and_retry(driver, wait, attempt):
                continue
            break
        except Exception as e:
            log.error(f"Error clicking 'Anfrage senden': {e}")
            if attempt == max_retries:
                raise

    # 2) Switch to iframe
    log.info("Switching to iframe...")
    wait.until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, "contact-iframe"))
    )
    time.sleep(0.3)

    # 3) Select Anrede = Herr
    log.info("Selecting 'Herr'...")
    try:
        dropdown_container = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "ng-select-container"))
        )
        human_click(driver, dropdown_container)
        time.sleep(0.3)
        herr_option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(),'Herr')]")
            )
        )
        human_click(driver, herr_option)
    except Exception as e:
        log.warning(f"Could not select 'Herr': {e}")

    # 4) Personal data
    first_name_input = find_element_with_fallback(
        wait,
        (By.ID, "firstName"),
        (By.XPATH, '//input[@formcontrolname="firstName"]'),
    )
    type_like_human(first_name_input, details["first_name"])

    surname_input = find_element_with_fallback(
        wait,
        (By.ID, "lastName"),
        (By.XPATH, '//input[@formcontrolname="lastName"]'),
    )
    type_like_human(surname_input, details["surname"])

    email_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//input[@formcontrolname="email"]')
        )
    )
    type_like_human(email_input, details["email"])

    street_input = find_element_with_fallback(
        wait,
        (By.ID, "street"),
        (By.XPATH, '//input[@formcontrolname="street"]'),
    )
    type_like_human(street_input, details["street"])

    house_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//input[@formcontrolname="houseNumber"]')
        )
    )
    type_like_human(house_input, details["house_number"])

    zip_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//input[@formcontrolname="zipCode"]')
        )
    )
    type_like_human(zip_input, details["postal_code"])

    city_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//input[@formcontrolname="city"]')
        )
    )
    type_like_human(city_input, details["city"])

    # 4b) Persons fields (mode-dependent)
    if wbs_mode:
        adults_value = str(details.get("total_persons", 1))
        log.info(f"Setting adults={adults_value}, children=0")
        safe_fill_field(
            wait,
            (By.ID, "formly_3_input_gewobag_anzahl_erwachsene_0"),
            adults_value,
            "adults",
        )
        safe_fill_field(
            wait,
            (By.ID, "formly_3_input_gewobag_anzahl_kinder_1"),
            "0",
            "children",
        )
        safe_fill_field(
            wait,
            (
                By.XPATH,
                "//input[@data-cy='formly_2_input_gewobag_gesamtzahl_der_"
                "einziehenden_personen_erwachsene_und_kinder_0']",
            ),
            details.get("total_persons", adults_value),
            "total persons (optional)",
        )
    else:
        total_input = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//input[@data-cy='formly_2_input_gewobag_gesamtzahl_der_"
                "einziehenden_personen_erwachsene_und_kinder_0']",
            ))
        )
        type_like_human(total_input, details["total_persons"])

    # Phone number
    phone_input = find_element_with_fallback(
        wait,
        (By.ID, "formly_17_input_$$_telephone_number_$$_0"),
        (By.XPATH, '//input[@formcontrolname="phoneNumber"]'),
    )
    type_like_human(phone_input, details["phone_number"])

    # 5) Application type: "Für mich selbst"
    log.info("Selecting 'Für mich selbst'...")
    try:
        dropdown = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//ng-select[contains(@id,"
                    "'fuer_wen_wird_die_wohnungsanfrage_gestellt')]",
                )
            )
        )
        human_click(driver, dropdown)
        time.sleep(0.3)
        option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(),'Für mich selbst')]")
            )
        )
        human_click(driver, option)
    except Exception as e:
        log.warning(f"Could not select application type: {e}")

    # 6) WBS-related extra questions (only in WBS mode)
    if wbs_mode:
        log.info("Answering WBS-related questions...")
        try:
            wbs_radio = wait.until(
                EC.presence_of_element_located(
                    (By.ID, "formly_4_radio_$$_wbs_available_$$_0-Nein")
                )
            )
            human_click(driver, wbs_radio)
            random_delay(0.2, 0.4)
        except Exception:
            log.info("  - WBS availability radio not found, skipping.")

        try:
            income_radio = wait.until(
                EC.presence_of_element_located((
                    By.ID,
                    "formly_9_radio_gewobag_haushaltsnettoeinkommen_"
                    "liegt_in_einkommensspanne_0-Ja",
                ))
            )
            human_click(driver, income_radio)
            random_delay(0.2, 0.4)
        except Exception:
            log.info("  - Income-spanne radio not found, skipping.")

    # 7) Privacy checkboxes (mode-dependent)
    log.info("Accepting privacy policies...")
    if wbs_mode:
        try:
            checkbox_iv = wait.until(
                EC.element_to_be_clickable((
                    By.ID,
                    "formly_20_checkbox_gewobag_datenschutzhinweis_"
                    "iv0027_bestaetigt_0",
                ))
            )
            human_click(driver, checkbox_iv)
            random_delay(0.2, 0.4)
        except Exception:
            log.info("  - IV0027 checkbox not found / could not click.")

        try:
            checkbox_main = wait.until(
                EC.element_to_be_clickable((
                    By.ID,
                    "formly_21_checkbox_gewobag_datenschutzhinweis_"
                    "bestaetigt_0",
                ))
            )
            human_click(driver, checkbox_main)
            random_delay(0.2, 0.4)
        except Exception as e:
            log.error(f"  - Could not click main privacy checkbox: {e}")
    else:
        try:
            checkbox = wait.until(
                EC.element_to_be_clickable((
                    By.ID,
                    "formly_20_checkbox_gewobag_datenschutzhinweis_bestaetigt_0",
                ))
            )
            human_click(driver, checkbox)
        except Exception as e:
            log.error(f"Could not click privacy checkbox: {e}")

    # 8) Submit
    log.info("Submitting application...")
    try:
        submit_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-cy='btn-submit']")
            )
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

    time.sleep(1.0)
    human_click(driver, submit_btn)
    time.sleep(1.5)


# --- User data / validation / main ---


def load_user_details(num_people):
    filename = f"user_details_{num_people}.json"
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        log.info(f"Loaded user details from {filename} ({len(data)} user(s))")
        return data
    except Exception as e:
        log.error(f"Error loading {filename}: {e}")
        return None


def validate_user(user, index):
    """Warn about missing/empty required fields. Returns True if usable."""
    missing = [f for f in REQUIRED_FIELDS if not str(user.get(f, "")).strip()]
    if missing:
        log.warning(f"User {index}: missing/empty fields: {missing}")
    if not str(user.get("email", "")).strip():
        log.error(f"User {index}: no email address, skipping.")
        return False
    return True


def get_user_input():
    print("=" * 50)
    print("Home Application Automation Tool (Firefox)")
    print("=" * 50)

    link = input("Please enter the application link: ").strip()
    if not link:
        print("No link provided.")
        return None, None, None, None

    if not link.startswith(("http://", "https://")):
        link = "https://" + link

    while True:
        n = input("How many people (1, 2, or 3): ").strip()
        if n in {"1", "2", "3"}:
            break
        print("Please enter 1, 2, or 3.")

    while True:
        mode = input("Form mode - WBS extra questions? (y/n): ").strip().lower()
        if mode in {"y", "n"}:
            break
        print("Please enter y or n.")

    headless = input("Run headless? (y/n, default n): ").strip().lower() == "y"

    return link, int(n), mode == "y", headless


def main():
    link, num_people, wbs_mode, headless = get_user_input()
    if link is None:
        return 1

    users = load_user_details(num_people)
    if not users:
        return 1

    mode_label = "WBS" if wbs_mode else "simple"
    log.info(f"Mode: {mode_label}, Users: {len(users)}, Headless: {headless}")

    for i, user in enumerate(users, start=1):
        if not validate_user(user, i):
            continue

        log.info(
            f"Processing user {i}/{len(users)}: "
            f"{user['first_name']} {user['surname']} - {user['email']}"
        )

        driver = create_firefox_driver(headless=headless)
        wait = WebDriverWait(driver, 15)

        try:
            driver.get(link)
            time.sleep(1.5)
            accept_cookies(driver)
            fill_form(driver, wait, user, wbs_mode=wbs_mode)
            log.info(f"Form submitted for {user['email']}")
        except Exception as e:
            log.error(f"Failed for {user['email']}: {e}")
        finally:
            driver.quit()

        if i < len(users):
            pause = random.uniform(1.0, 2.0)
            log.info(f"Waiting {pause:.1f}s before next user...")
            time.sleep(pause)

    log.info("All applications completed!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
