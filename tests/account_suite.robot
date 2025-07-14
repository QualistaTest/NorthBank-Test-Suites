
*** Settings ***
Library    SeleniumLibrary
Resource   ../resources/SecureBankApp.robot
Resource   ../resources/AccountPage.robot

Suite Setup     Launch App And Login Page
Suite Teardown  Close Browser

*** Test Cases ***
Open New Account
    [Tags]    Demo-28    DEMO-7
    Login As Valid User
    Open New Account
    Page Should Contain    Account successfully created