
*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${OPEN_ACCOUNT_BTN}     xpath=//nav//a[normalize-space()='Open Account'] 
${SUBMIT_ACCOUNT_BTN}   xpath=//button[contains(text(),'Submit')]

*** Keywords ***
Open New Account
    Wait Until Element Is Visible    xpath=//nav//a[normalize-space()='Open Account']    5s
    Click Element    ${OPEN_ACCOUNT_BTN}
    Click Button     ${SUBMIT_ACCOUNT_BTN}
