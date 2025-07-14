*** Settings ***
Library    SeleniumLibrary
Resource   ../resources/SecureBankApp.robot

Suite Setup     Launch App And Login Page
Suite Teardown  Close Browser

# Test Setup      Maximize Browser Window
# Suite Teardown     Close Browser
# Test Setup         Launch App And Login Page
# Test Teardown      Close Browser  # Optional, depends on how isolated you want each test 

*** Test Cases ***

# Go to login page
#     Launch App And Login Page

Valid Login
    [Tags]    Demo-29    DEMO-10
    Login As Valid User

Invalid Login With Wrong Password
    [Tags]    Demo-30    DEMO-10
    Login With Credentials    ${VALID_USER}    ${INVALID_PASS}
    Page Should Contain    ${VALIDATION_TEXT}

Logout
    [Tags]    Demo-31    DEMO-10
    Logout
