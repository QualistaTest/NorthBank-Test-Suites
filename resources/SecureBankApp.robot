
*** Settings ***
Library    SeleniumLibrary
Library    ../resources/custom_chrome.py

*** Variables ***
${URL}            https://qualista.tech/test-mb3/
${BROWSER}        Chrome
${VALID_USER}     demo@qualista.tech
${VALID_PASS}     password123
${INVALID_PASS}   wrongpassword
${NAME}           John


${SIGN_IN_BUTTON}    xpath=//button[normalize-space()='Sign In']
${LOGOUT_BUTTON}     xpath=//button[normalize-space()='Sign Out']
${EMAIL_INPUT}       //input[@id='signin-email']
${PASS_INPUT}        //input[@id='signin-password']
${LOGIN_BTN}         //button[@type='submit']
${WELCOME_MESSAGE}   Welcome back, ${NAME}
${WELCOME}           xpath=//*[contains(text(),'Welcome back,')]
${WELCOME_TEXT}      Here's what's happening with your accounts today.
${VALIDATION_TEXT}    Validation failed. Please check your credentials and try again.

*** Keywords ***
Launch App And Login Page
    ${options}=    Get Chrome Options
    Create WebDriver    Chrome    options=${options}
    Go To    ${URL}
    Wait Until Page Contains Element    ${SIGN_IN_BUTTON}    10s
    Maximize Browser Window
    Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    10s
    Click Element                    ${SIGN_IN_BUTTON}
    Wait Until Element Is Visible    ${EMAIL_INPUT}       5s
Login As Valid User
    Input Text    ${EMAIL_INPUT}    ${VALID_USER}
    Input Text    ${PASS_INPUT}     ${VALID_PASS}
    Click Element    ${LOGIN_BTN}
    Wait Until Page Contains    ${WELCOME_MESSAGE}    5s
    Wait Until Page Contains    ${WELCOME_TEXT}    5s
    Element Text Should Be    xpath=//div[@id='main-content']//h2    ${WELCOME_MESSAGE}
    Element Text Should Be    xpath=//div[@id='main-content']//p    ${WELCOME_TEXT}

Login With Credentials
    [Arguments]    ${email}    ${password}
    Input Text    ${EMAIL_INPUT}    ${email}
    Input Text    ${PASS_INPUT}     ${password}
    Click Element    ${LOGIN_BTN}
    Wait Until Page Contains    ${WELCOME_MESSAGE}    5s
    Wait Until Page Contains    ${WELCOME_TEXT}    5s

# Logout
#     Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    10s
#     Click Element                    ${SIGN_IN_BUTTON}
#     # Execute JavaScript    arguments[0].click();    ${SIGN_IN_BUTTON}

#     Wait Until Element Is Visible    ${LOGIN_BTN}    10s

#     Wait Until Element Is Visible    ${EMAIL_INPUT}       10s
#     Wait Until Element Is Enabled    ${EMAIL_INPUT}       5s
#     Click Element                    ${EMAIL_INPUT}
#     Input Text    ${EMAIL_INPUT}    ${VALID_USER}
#     Input Text    ${PASS_INPUT}     ${VALID_PASS}

#     Capture Page Screenshot
#     Click Element    ${LOGIN_BTN}

#     Wait Until Element Is Visible    ${LOGOUT_BUTTON}    10s
#     Click Element   ${LOGOUT_BUTTON}

#     Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    10s/
#     Element Should Not Be Visible    ${WELCOME}

Logout
    Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    10s

    ${modal_visible}=    Run Keyword And Return Status    Element Should Be Visible    xpath=//div[@id="signin-modal" and contains(@class, "active")]
    Run Keyword Unless    ${modal_visible}    Click Element    ${SIGN_IN_BUTTON}

    Wait Until Element Is Visible    xpath=//div[@id="signin-modal" and contains(@class, "active")]    5s
    Wait Until Element Is Visible    ${EMAIL_INPUT}       10s
    Wait Until Element Is Enabled    ${EMAIL_INPUT}        5s
    Click Element                    ${EMAIL_INPUT}
    Input Text                       ${EMAIL_INPUT}        ${VALID_USER}
    Input Text                       ${PASS_INPUT}         ${VALID_PASS}

    Capture Page Screenshot
    Click Element                    ${LOGIN_BTN}

    Wait Until Element Is Visible    ${LOGOUT_BUTTON}     10s
    Click Element                    ${LOGOUT_BUTTON}

    Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    10s
    Page Should Contain Element      ${SIGN_IN_BUTTON}