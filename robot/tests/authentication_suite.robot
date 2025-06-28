*** Settings ***
Library    SeleniumLibrary
Resource   ../resources/SecureBankApp.robot

Suite Setup     Launch App And Login Page
Suite Teardown  Close Browser
Test Setup      Maximize Browser Window

*** Test Cases ***

Go to login page
    Launch App And Login Page

Valid Login
    Login As Valid User

Logout
    Logout

Invalid Login With Wrong Password
    Login With Credentials    ${VALID_USER}    ${INVALID_PASS}
    Page Should Contain    ${VALIDATION_TEXT}


