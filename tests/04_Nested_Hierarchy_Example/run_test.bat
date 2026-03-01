@echo off
pushd %~dp0
echo Running test...
python ../../main.py --config ../../config/default_rules.yaml --reqs requirements.csv --source src --output ../test_outputs
popd
