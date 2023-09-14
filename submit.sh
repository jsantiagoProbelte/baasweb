# ./translate.sh
./run_test.sh 
if [ $? -eq 0 ]; then
    git push
else
    echo "========== ERROR ON COVERAGE"
    exit 2
fi
#
