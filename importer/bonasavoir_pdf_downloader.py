"""Download all PDFs from the Bon à Savoir website for the years 2014-2024."""

import os
import re
from pathlib import Path
from urllib.parse import urljoin

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

debugging = True


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be used as a filename."""
    return re.sub(r'[\\/:"*?<>|]+', "_", name)


def download_pdfs(driver: webdriver, pdf_dir: str) -> None:
    """Download PDFs from the current page."""
    pdf_blocks = driver.find_elements(
        By.CSS_SELECTOR,
        'div[style*="margin-bottom: 30px;"]',
    )
    print(f"Found {len(pdf_blocks)} potential PDF blocks")

    for block in pdf_blocks:
        p_tag = block.find_element(By.TAG_NAME, "p")
        link_tag = block.find_element(By.CSS_SELECTOR, "p + .textlink")

        if p_tag and link_tag:
            pdf_name = sanitize_filename(p_tag.text.strip().replace(" ", ""))
            pdf_url = urljoin(driver.current_url, link_tag.get_attribute("href"))
            pdf_path = pdf_dir / (pdf_name + ".pdf")

            print(f"PDF name: {pdf_name}, URL: {pdf_url}")

            if pdf_path.exists():
                print(f"Skipping {pdf_name}, already exists.")
                continue

            driver.get(pdf_url)
            content_type = driver.execute_script("return document.contentType;")
            print(f"Content type of {pdf_name}: {content_type}")

            if content_type == "application/pdf":
                with pdf_path.open("wb") as pdf_file:
                    pdf_file.write(driver.page_source.encode("utf-8"))
                print(f"Downloaded {pdf_name}")
            else:
                print(
                    f"""Failed to download {pdf_name}: URL returned non-PDF
                    content or not authenticated.""",
                )


def main() -> None:
    """Download all PDFs from the Bon à Savoir website for the years 2014-2024."""
    load_dotenv()

    bonasavoir_username = os.getenv("BONASAVOIR_USERNAME")
    bonasavoir_password = os.getenv("BONASAVOIR_PASSWORD")

    if not bonasavoir_username or not bonasavoir_password:
        raise Exception("Missing credentials in .env file")

    chrome_options = Options()
    if debugging:
        chrome_options.add_experimental_option("detach", True)
    else:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

    script_directory = Path(__file__).resolve().parent.parent
    driver_path = script_directory / "chromedriver-mac-arm64" / "chromedriver"

    service = ChromeService(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Login
        driver.get("https://www.bonasavoir.ch/connexion")
        WebDriverWait(driver, 10).until(
            ec.presence_of_element_located(
                (By.NAME, "tx_updkonsuminfo_konsuminfofe[userid]"),
            ),
        )

        username_field = driver.find_element(
            By.NAME,
            "tx_updkonsuminfo_konsuminfofe[userid]",
        )
        password_field = driver.find_element(
            By.NAME,
            "tx_updkonsuminfo_konsuminfofe[password]",
        )
        login_button = driver.find_element(By.NAME, "logIn")

        username_field.send_keys(bonasavoir_username)
        password_field.send_keys(bonasavoir_password)
        login_button.click()

        # Update the WebDriverWait to wait for the specific login message
        WebDriverWait(driver, 10).until(
            ec.text_to_be_present_in_element(
                (By.TAG_NAME, "p"),
                "Vous êtes maintenant connecté.",
            ),
        )

        base_url = "https://www.bonasavoir.ch"
        pdf_dir = Path(__file__).resolve().parent.parent / "pdf_downloads"
        pdf_dir.mkdir(parents=True, exist_ok=True)

        current_year = 2024
        while current_year >= 2014:
            year_url = f"{base_url}/epaper/archive/{current_year}"
            driver.get(year_url)
            WebDriverWait(driver, 10).until(
                ec.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[style*="margin-bottom: 30px;"]'),
                ),
            )
            print(f"Processing year {current_year}")
            # Download PDFs for the current year
            download_pdfs(driver, pdf_dir)
            current_year -= 1

        print("All PDFs downloaded successfully.")
    finally:
        if not debugging:
            driver.quit()


if __name__ == "__main__":
    main()
