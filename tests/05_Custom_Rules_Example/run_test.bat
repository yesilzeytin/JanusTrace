@echo off
pushd %~dp0
echo Running test...
python ../../main.py --config custom_rules.yaml --reqs requirements.csv --source src --output ../test_outputs
popd
