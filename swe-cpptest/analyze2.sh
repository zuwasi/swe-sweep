#!/bin/bash
# analyze2.sh <name> [bdf] : MISRA C 2025, MISRA C++ 2023, Flow Analysis Aggressive
NAME=$1; BDF=${2:-cc.bdf}
ROOT=/home/danie/swe-cpptest; CPT=/home/danie/parasoft/cpptest
cd $ROOT/$NAME || exit 1
IMPORT=(-property bdf.import.compiler.family=gcc_13-64
        -property bdf.import.c.compiler.exec=/usr/bin/cc
        -property bdf.import.cpp.compiler.exec=/usr/bin/c++)
for CFG in "MISRA C 2025" "MISRA C++ 2023" "Flow Analysis Aggressive"; do
  TAG=$(echo $CFG | tr ' ' '_'); TAG=${TAG/+/p}
  rm -rf ws-$TAG
  $CPT/cpptestcli -config "builtin://$CFG" -bdf $BDF "${IMPORT[@]}" \
      -data $ROOT/$NAME/ws-$TAG -report $ROOT/$NAME/report-$TAG > run-$TAG.log 2>&1
  echo "$NAME [$CFG]: $(grep -o 'Source Files to Check: [0-9]*' run-$TAG.log|tail -1), $(grep -o 'Violations Found: [0-9]*' run-$TAG.log|tail -1)"
done
