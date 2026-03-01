@echo off
pushd %~dp0
echo =================================
echo Running All Examples
echo =================================

cd 01_SystemVerilog_Example && call run_test.bat && cd ..
cd 02_VHDL_Example && call run_test.bat && cd ..
cd 03_Mixed_Language_Example && call run_test.bat && cd ..
cd 04_Nested_Hierarchy_Example && call run_test.bat && cd ..
cd 05_Custom_Rules_Example && call run_test.bat && cd ..
cd 06_Missing_Req_Example && call run_test.bat && cd ..
cd 07_Orphan_Trace_Example && call run_test.bat && cd ..
cd 08_Invalid_Req_Format_Example && call run_test.bat && cd ..
cd 09_Invalid_Trace_Format_Example && call run_test.bat && cd ..
cd 10_All_Errors_Combined_Example && call run_test.bat && cd ..
cd 11_IBM_DOORS_Example && call run_test.bat && cd ..

echo =================================
echo All tests completed. Checks test_outputs/ folder.
echo =================================
popd
