*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${URL}            https://qualista.tech/test-mb3/
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
${WELCOME_TEXT}      Here's what's happening with your accounts today.
${VALIDATION_TEXT}   Validation failed. Please check your credentials and try again.

*** Keywords ***
Launch App And Login Page
    ${RANDOM}=    Evaluate    str(uuid.uuid4())[:8]    modules=uuid
    ${CHROME_PROFILE_DIR}=    Set Variable    /tmp/chrome-profile-${RANDOM}
    ${OPTIONS}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    modules=sys,selenium.webdriver
    Call Method    ${OPTIONS}    add_argument    "--headless=new"
    Call Method    ${OPTIONS}    add_argument    "--user-data-dir=${CHROME_PROFILE_DIR}"
    Call Method    ${OPTIONS}    add_argument    "--no-sandbox"
    Call Method    ${OPTIONS}    add_argument    "--disable-dev-shm-usage"
    Call Method    ${OPTIONS}    add_argument    "--disable-gpu"
    Create Webdriver    Chrome    executable_path=/usr/bin/chromedriver    options=${OPTIONS}
    Go To    ${URL}
    Maximize Browser Window
    Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    5s
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

Logout
    Input Text    ${EMAIL_INPUT}    ${VALID_USER}
    Input Text    ${PASS_INPUT}     ${VALID_PASS}
    Click Element    ${LOGIN_BTN}
    Wait Until Element Is Visible    ${LOGOUT_BUTTON}    5s
    Click Element   ${LOGOUT_BUTTON}
    Wait Until Page Does Not Contain    ${WELCOME_MESSAGE}    5s
    Wait Until Page Does Not Contain    ${WELCOME_TEXT}    5s
    Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    5s
    [Teardown]    Close Browser
