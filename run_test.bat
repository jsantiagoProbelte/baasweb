@echo off
setlocal

 

set MINIMIN_COVERAGE=95

 

:: Stop the build if there are Python syntax errors or undefined names
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --max-line-length=127 --exclude venv_baas,migrations
if %errorlevel% neq 0 (
    echo ========== ERROR FLAKE8 - python syntax error
    exit /b 2
)

 

:: Exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
:: --exit-zero ... treats errors as warnings
flake8 . --count --max-complexity=10 --max-line-length=127 --statistics --exclude venv_baas,migrations
if %errorlevel% neq 0 (
    echo ========== ERROR FLAKE8 - complexity
    exit /b 2
)

 

python -m coverage run -m pytest . --junitxml=./reports_tests/junit.xml
if %errorlevel% neq 0 (
    echo ========== ERROR ON UNIT TEST
    exit /b 2
)

 

python -m coverage report --show-missing --fail-under=%MINIMIN_COVERAGE%
set COVERAGE=%errorlevel%
if %COVERAGE% neq 0 (
    echo ========== ERROR ON COVERAGE
)

 

python -m coverage html -d reports_tests

 

exit /b %COVERAGE%