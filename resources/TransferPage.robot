*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${EMAIL_INPUT}        id=recipient-email
${IBAN_INPUT}         id=iban
${AMOUNT_INPUT}       id=amount
${NOTE_INPUT}         id=note
${SEND_BUTTON}        xpath=//button[normalize-space()='Send Money']
${SEND_MONEY_LINK}   xpath=//nav//button[normalize-space(.)='Transfer']
${POPUP_TITLE}        Transfer Successful!
${POPUP_MESSAGE}      Your money has been sent successfully
${POPUP_DONE_BUTTON}  xpath=//button[normalize-space()='Done']

*** Keywords ***
Send Money
    [Tags]    Demo-32
    [Arguments]    ${email}    ${iban}    ${amount}    ${note}=Thanks
    # Navigate to Transfer tab first
    Click Element    ${SEND_MONEY_LINK}
    Wait Until Element Is Visible    id=recipient-email    5s
    Click Element                    id=recipient-email
    Input Text                       id=recipient-email    ${email}

    Click Element                    id=recipient-iban
    Input Text                       id=recipient-iban    ${iban}

    Click Element                    id=transfer-amount
    Input Text                       id=transfer-amount    ${amount}

    Click Element                    id=transfer-note
    Input Text                       id=transfer-note    ${note}

    Click Button                     xpath=//button[@onclick='sendMoney()']

Verify Transfer Success Popup
    [Tags]    Demo-33
    Wait Until Page Contains    ${POPUP_TITLE}    5s
    Wait Until Page Contains    ${POPUP_MESSAGE}    5s
    Click Button                ${POPUP_DONE_BUTTON}