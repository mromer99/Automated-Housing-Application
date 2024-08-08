import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load user details from JSON file
with open('user_details_1.json', 'r') as file:
    user_details = json.load(file)

# Load links from JSON file
with open('links.json', 'r') as file:
    links = json.load(file)

def fill_form(driver, wait, details):
    try:
        # Click "Anfrage senden" button
        anfrage_senden = wait.until(EC.element_to_be_clickable((By.XPATH, "(//button[contains(text(), 'Anfrage senden')])[1]")))
        driver.execute_script("arguments[0].click();", anfrage_senden)
        time.sleep(1)  # Add delay

        # Switch driver into IFRAME
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "contact-iframe")))

        # Click "Bitte auswählen"
        wait.until(EC.visibility_of_element_located((By.XPATH, "//div[text()='Bitte auswählen']"))).click()

        # Click dropdown option "Herr"
        wait.until(EC.element_to_be_clickable((By.XPATH, "//li[contains(text(),'Herr')]"))).click()

        # Fill first name
        first_name_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="firstName"]')))
        first_name_input.clear()
        first_name_input.send_keys(details['first_name'])

        # Fill surname
        surname_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="lastName"]')))
        surname_input.clear()
        surname_input.send_keys(details['surname'])

        # Fill email
        email_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="email"]')))
        email_input.clear()
        email_input.send_keys(details['email'])

        # Fill phone number
        phone_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="phoneNumber"]')))
        phone_input.clear()
        phone_input.send_keys(details['phone_number'])

        # Fill street
        street_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="street"]')))
        street_input.clear()
        street_input.send_keys(details['street'])

        # Fill house number
        house_number_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="houseNumber"]')))
        house_number_input.clear()
        house_number_input.send_keys(details['house_number'])

        # Fill postal code
        postal_code_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="zipCode"]')))
        postal_code_input.clear()
        postal_code_input.send_keys(details['postal_code'])

        # Fill city
        city_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="city"]')))
        city_input.clear()
        city_input.send_keys(details['city'])

        # Fill total number of persons
        total_persons_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="formly_2_input_gewobag_gesamtzahl_der_einziehenden_personen_erwachsene_und_kinder_0"]')))
        total_persons_input.clear()
        total_persons_input.send_keys(details['total_persons'])

        # Click the dropdown to select "Stellen Sie diese Wohnungsanfrage..."
        wait.until(EC.element_to_be_clickable((By.XPATH, "//nz-select[@id='formly_3_select_gewobag_fuer_wen_wird_die_wohnungsanfrage_gestellt_0']"))).click()

        # Select "Für mich selbst oder meine Angehörigen"
        wait.until(EC.element_to_be_clickable((By.XPATH, "//li[contains(text(), 'Für mich selbst oder meine Angehörigen ')]"))).click()

        # Click on checkbox to accept the privacy policy
        checkbox_label = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[@id='formly_12_checkbox_gewobag_datenschutzhinweis_bestaetigt_0']")))
        checkbox_label.click()
        time.sleep(1)  # Add delay
        print("Checkbox clicked")

        # Click on "Anfrage versenden"
        anfrage_versenden_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-cy='btn-submit']")))
        anfrage_versenden_button.click()
        print("Anfrage versenden button clicked")

    except Exception as e:
        print(f"An error occurred while filling the form: {e}")
        

# Main script to process each link and each user
for link in links:
    for user in user_details:
        # Initialize the WebDriver for Firefox
        driver = webdriver.Firefox()
        # minimize the window
        driver.maximize_window()
        wait = WebDriverWait(driver, 20)

        # Navigate to the form page
        driver.get(link)

        # Click "Alle Cookies akzeptieren"
        wait.until(EC.element_to_be_clickable((By.XPATH, "(//a[contains(text(),'Alle Cookies akzeptieren')])[1]"))).click()

        # Fill the form for the current user
        fill_form(driver, wait, user)

        # Close the driver
        driver.quit()
        print(f"Form submitted for {user['email']} on {link}")

        # Pause for a short duration before processing the next user
        time.sleep(1)

    # Pause for a short duration before processing the next link
    time.sleep(5)
