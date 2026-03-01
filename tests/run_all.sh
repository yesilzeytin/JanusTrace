#!/bin/bash
cd "$(dirname "$0")"
echo "================================="
echo "Running All Examples"
echo "================================="

(cd 01_SystemVerilog_Example && ./run_test.sh)
(cd 02_VHDL_Example && ./run_test.sh)
(cd 03_Mixed_Language_Example && ./run_test.sh)
(cd 04_Nested_Hierarchy_Example && ./run_test.sh)
(cd 05_Custom_Rules_Example && ./run_test.sh)
(cd 06_Missing_Req_Example && ./run_test.sh)
(cd 07_Orphan_Trace_Example && ./run_test.sh)
(cd 08_Invalid_Req_Format_Example && ./run_test.sh)
(cd 09_Invalid_Trace_Format_Example && ./run_test.sh)
(cd 10_All_Errors_Combined_Example && ./run_test.sh)
(cd 11_IBM_DOORS_Example && ./run_test.sh)

echo "================================="
echo "All tests completed. Checks test_outputs/ folder."
echo "================================="
