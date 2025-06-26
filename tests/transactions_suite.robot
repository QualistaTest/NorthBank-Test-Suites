
*** Settings ***
Library    SeleniumLibrary
Resource   ../resources/SecureBankApp.robot
Resource   ../resources/TransactionsPage.robot

Suite Setup     Launch App And Login Page
Suite Teardown  Close Browser

*** Test Cases ***
Filter Transactions By Amount Range
    [Tags]    Demo-34
    Login As Valid User
    Go To Transactions
    Filter Transactions By Amount Range    $200 - $500
    Verify Transactions Are In Selected Amount Range    $200 - $500

Export Transactions To CSV
    [Tags]    Demo-35
    Login As Valid User
    Go To Transactions
    Export Transactions
    # Check manually or by download validation
