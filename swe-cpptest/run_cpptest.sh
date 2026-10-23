#!/bin/bash
# Run Parasoft C++test (Professional 2025.2) static analysis on a SWE-sweep C/C++ repo.
# Usage: run_cpptest.sh <name> <git-ref> <clone-url> [cmake-args...]
set -u
NAME=$1; REF=$2; URL=$3; shift 3
ROOT=/home/danie/swe-cpptest
CPT=/home/danie/parasoft/cpptest
REPO=$ROOT/$NAME
BDF_IMPORT=(-property bdf.import.compiler.family=gcc_13-64
            -property bdf.import.c.compiler.exec=/usr/bin/cc
            -property bdf.import.cpp.compiler.exec=/usr/bin/c++)

mkdir -p $ROOT
if [ ! -d $REPO/.git ]; then
  git clone --quiet --depth 1 --branch "$REF" "$URL" $REPO || { echo "$NAME: clone failed"; exit 1; }
fi
cd $REPO || exit 1

# Configure (records compile_commands.json) then build so generated headers exist.
cmake -S . -B build -G "Unix Makefiles" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON "$@" > cfg.log 2>&1 \
  || { echo "$NAME: configure failed"; tail -5 cfg.log; exit 1; }
make -C build -j 24 > build.log 2>&1 || echo "$NAME: build incomplete (continuing with recorded TUs)"

python3 $ROOT/cc2bdf.py build/compile_commands.json "$NAME" cc.bdf $REPO || exit 1

for CFG in "Recommended Rules" "Flow Analysis Standard" "Flow Analysis Aggressive"; do
  TAG=$(echo $CFG | tr ' ' '_')
  rm -rf $ROOT/$NAME/ws-$TAG
  $CPT/cpptestcli -config "builtin://$CFG" -bdf cc.bdf "${BDF_IMPORT[@]}" \
      -data $ROOT/$NAME/ws-$TAG \
      -report $ROOT/$NAME/report-$TAG > run-$TAG.log 2>&1
  V=$(grep -o "Violations Found: [0-9]*" run-$TAG.log | tail -1)
  F=$(grep -o "Source Files to Check: [0-9]*" run-$TAG.log | tail -1)
  echo "$NAME [$CFG]: $F, $V"
done
