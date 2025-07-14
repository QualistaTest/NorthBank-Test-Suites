
*** Settings ***
Library    SeleniumLibrary
Resource   ../resources/SecureBankApp.robot
Resource   ../resources/TransferPage.robot

Suite Setup     Launch App And Login Page
Suite Teardown  Close Browser

*** Variables ***
${RECIPIENT_EMAIL}   test@example.com
${RECIPIENT_IBAN}    DE12345678901234567890
${TRANSFER_AMOUNT}   50
${LARGE_AMOUNT}      999999
${REASON}            Pizza party

*** Test Cases ***
Send Money Successfully
    [Tags]    Demo-32    DEMO-9
    Login As Valid User
    Send Money    ${RECIPIENT_EMAIL}    ${RECIPIENT_IBAN}    ${TRANSFER_AMOUNT}    ${REASON}
    Verify Transfer Success Popup

Transfer With Insufficient Funds
    [Tags]    Demo-33    DEMO-9
    Login As Valid User
    Send Money    ${RECIPIENT_EMAIL}    ${RECIPIENT_IBAN}    ${LARGE_AMOUNT}    ${REASON}
    Page Should Contain    Insufficient funds

