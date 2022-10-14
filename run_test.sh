
# stop the build if there are Python syntax errors or undefined names
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --max-line-length=127 --exclude venv_baas
if [ $? -ne 0 ]; then
    echo "========== ERROR FLAKE8 - python syntax error"
    exit 2
fi

# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
# --exit-zero ... treats errors as warnings
flake8 . --count --max-complexity=10 --max-line-length=127 --statistics --exclude venv_baas
if [ $? -ne 0 ]; then
    echo "========== ERROR FLAKE8 -complexity"
    exit 2
fi

python -m coverage run  -m pytest . --junitxml=./reports_tests/junit.xml 
if [ $? -ne 0 ]; then
    echo "========== ERROR ON UNIT TEST"
    exit 2
fi
    
python -m coverage report  --show-missing --fail-under=90
COVERAGE=$?
if [ $COVERAGE -ne 0 ]; then    
    echo "========== ERROR ON COVERAGE"
fi
python -m coverage html -d reports_tests

exit $COVERAGE

