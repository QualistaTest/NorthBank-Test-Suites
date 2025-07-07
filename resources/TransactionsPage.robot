
*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${TRANSACTIONS_LINK}    xpath=//nav//button[normalize-space(.)='Transactions']
${AMOUNT_MIN_FIELD}     id=amountMin
${AMOUNT_MAX_FIELD}     id=amountMax
${APPLY_FILTER_BTN}     xpath=//button[contains(text(),'Apply')]
${EXPORT_CSV_BTN}       xpath=//button[contains(text(),'Export CSV')]

*** Keywords ***
Go To Transactions
    Wait Until Element Is Visible    ${TRANSACTIONS_LINK}    5s
    Click Element    ${TRANSACTIONS_LINK}
    Wait Until Page Contains    All Transactions

Filter Transactions By Amount Range
    [Tags]    Demo-34
    [Arguments]    ${range}
    Wait Until Element Is Visible    xpath=//label[contains(., 'Amount Range')]/following-sibling::select    5s
    Select From List By Label        xpath=//label[contains(., 'Amount Range')]/following-sibling::select    ${range}

Verify Transactions Are In Selected Amount Range
    [Arguments]    ${range_label}

    IF    '${range_label}' == '$0 - $50'
        ${min}=    Set Variable    0
        ${max}=    Set Variable    50
    ELSE IF    '${range_label}' == '$50 - $200'
        ${min}=    Set Variable    50
        ${max}=    Set Variable    200
    ELSE IF    '${range_label}' == '$200 - $500'
        ${min}=    Set Variable    200
        ${max}=    Set Variable    500
    ELSE IF    '${range_label}' == '$500+'
        ${min}=    Set Variable    500
        ${max}=    Set Variable    1000000
    END

    ${amount_elements}=    Get WebElements    xpath=//div[contains(@class, 'TransactionHistory')]//div[contains(text(), '$')]
    FOR    ${element}    IN    @{amount_elements}
        ${raw_text}=    Get Text    ${element}
        ${amount}=    Evaluate    abs(float(${raw_text}.replace('$', '').replace(',', '').replace('+', '').replace('-', '')))
        Should Be True    ${amount} >= ${min} and ${amount} <= ${max}
    END

Export Transactions
    [Tags]    Demo-35
    Click Button    ${EXPORT_CSV_BTN}
    Sleep    1s

