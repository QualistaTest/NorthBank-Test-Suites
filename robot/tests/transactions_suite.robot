
*** Settings ***
Library    SeleniumLibrary
Resource   ../resources/SecureBankApp.robot
Resource   ../resources/TransactionsPage.robot

Suite Setup     Launch App And Login Page
Suite Teardown  Close Browser

*** Test Cases ***
Filter Transactions By Amount Range
    Login As Valid User
    Go To Transactions
    Filter Transactions By Amount Range    $200 - $500
    Verify Transactions Are In Selected Amount Range    $200 - $500

Export Transactions To CSV
    Login As Valid User
    Go To Transactions
    Export Transactions
    # Check manually or by download validation
