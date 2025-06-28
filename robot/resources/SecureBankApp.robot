*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${URL}            https://qualista.tech/test-mb3/
${VALID_USER}     demo@qualista.tech
${VALID_PASS}     password123
${INVALID_PASS}   wrongpassword
${NAME}           John

${SIGN_IN_BUTTON}    xpath=//button[normalize-space()='Sign In']
${LOGOUT_BUTTON}     xpath=//*[normalize-space(text())='Sign Out']
${EMAIL_INPUT}       //input[@id='signin-email']
${PASS_INPUT}        //input[@id='signin-password']
${LOGIN_BTN}         //button[@type='submit']
${WELCOME_MESSAGE}   Welcome back, ${NAME}
${WELCOME_TEXT}      Here's what's happening with your accounts today.
${VALIDATION_TEXT}   Validation failed. Please check your credentials and try again.

*** Keywords ***
Launch App And Login Page
    ${options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    modules=sys, selenium.webdriver
    Call Method    ${options}    add_argument    --headless
    Call Method    ${options}    add_argument    --no-sandbox
    Call Method    ${options}    add_argument    --disable-dev-shm-usage
    Call Method    ${options}    add_argument    --disable-gpu

    Create WebDriver    Chrome    options=${options}   


    Go To    ${URL}
    Maximize Browser Window
    Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    timeout=5s
    Click Element                    ${SIGN_IN_BUTTON}
    Wait Until Element Is Visible    ${EMAIL_INPUT}       timeout=5s




Login As Valid User
    Input Text    ${EMAIL_INPUT}    ${VALID_USER}
    Input Text    ${PASS_INPUT}     ${VALID_PASS}
    Click Element    ${LOGIN_BTN}
    Wait Until Page Contains    ${WELCOME_MESSAGE}    5s
    Wait Until Page Contains    ${WELCOME_TEXT}    5s
    Element Text Should Be    xpath=//div[@id='main-content']//h2    ${WELCOME_MESSAGE}
    Element Text Should Be    xpath=//div[@id='main-content']//p    ${WELCOME_TEXT}


Logout
    Wait Until Element Is Visible    ${LOGOUT_BUTTON}    4s
    Click Element   ${LOGOUT_BUTTON}
    Wait Until Page Does Not Contain    ${WELCOME_MESSAGE}    5s
    Wait Until Page Does Not Contain    ${WELCOME_TEXT}    5s
    Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    5s
    [Teardown]    Close Browser


Login With Credentials
    [Arguments]    ${email}    ${password}
    Input Text    ${EMAIL_INPUT}    ${email}
    Input Text    ${PASS_INPUT}     ${password}
    Click Element    ${LOGIN_BTN}
    Wait Until Page Contains    ${WELCOME_MESSAGE}    5s
    Wait Until Page Contains    ${WELCOME_TEXT}    5s


