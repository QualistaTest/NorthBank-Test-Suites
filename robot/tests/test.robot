*** Settings ***
Library    SeleniumLibrary

*** Test Cases ***
Open Chrome
    Open Browser    https://example.com    Chrome    options=add_argument("--headless"),add_argument("--no-sandbox"),add_argument("--disable-dev-shm-usage")
    Title Should Be    Example Domain
    Close Browser
