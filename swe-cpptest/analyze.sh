#!/bin/bash
# analyze.sh <name> : run 3 configs on existing cc.bdf with isolated workspaces
NAME=$1; ROOT=/home/danie/swe-cpptest; CPT=/home/danie/parasoft/cpptest
cd $ROOT/$NAME || exit 1
IMPORT=(-property bdf.import.compiler.family=gcc_13-64
        -property bdf.import.c.compiler.exec=/usr/bin/cc
        -property bdf.import.cpp.compiler.exec=/usr/bin/c++)
for CFG in "Recommended Rules" "Flow Analysis Standard" "Flow Analysis Aggressive"; do
  TAG=$(echo $CFG | tr ' ' '_'); rm -rf ws-$TAG
  $CPT/cpptestcli -config "builtin://$CFG" -bdf cc.bdf "${IMPORT[@]}" \
      -data $ROOT/$NAME/ws-$TAG -report $ROOT/$NAME/report-$TAG > run-$TAG.log 2>&1
  echo "$NAME [$CFG]: $(grep -o 'Source Files to Check: [0-9]*' run-$TAG.log|tail -1), $(grep -o 'Violations Found: [0-9]*' run-$TAG.log|tail -1)"
done
