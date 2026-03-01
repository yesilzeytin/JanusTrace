#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
python3 "$DIR/../../main.py" --config "$DIR/../../config/default_rules.yaml" --reqs "$DIR/requirements.csv" --source "$DIR/src" --output "$DIR/../test_outputs"
