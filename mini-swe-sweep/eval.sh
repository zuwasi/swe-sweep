#!/bin/bash
# mini-swe-sweep eval: score one patch against one task's chosen 5 bugs.
# usage: eval.sh <repo> <agent>
set -u
export PATH="$HOME/.local/bin:$PATH"
SWEEP=/mnt/c/Users/danie/amp-demos/swe-sweep
ROOT=/home/danie/mini-swe-sweep
REPO=$1
AGENT=$2
declare -A BUGS=(
  [libexpat]="libexpat-0c5dbd0bb0a5,libexpat-30d93b149d3d,libexpat-44558a21f1b7,libexpat-4e25524fb119,libexpat-69f40cffb664"
  [click]="click-0099eb6f2003,click-4f1302f13075,click-6017fe42f482,click-679517d3ee49,click-747fcbb3e083"
  [gson]="gson-797489de243a,gson-89ed2dfbe1b3,gson-b22995c188d0,gson-f14521f7bdc3,gson-f9267b01483c"
  [roslyn]="roslyn-13e38774dd0d,roslyn-19392d53f4a9,roslyn-2068fcc3b53f,roslyn-21d406d9d4b2,roslyn-2730ba811675"
  [z3]="z3-21693e1cea96,z3-6aeffc53878d,z3-7c5e71fa9a15,z3-845ca575f448,z3-9b51ad4d5969"
  [tokio]="tokio-2b6ad5dad2ed,tokio-2be615ee964c,tokio-31f4c3861d7c,tokio-3abde857735e,tokio-437cb4b92ee3"
  [hdf5]="hdf5-336148f0f3e2,hdf5-3d50b7243378,hdf5-410d9d0e6a1f,hdf5-46ec0c6c502b,hdf5-50b75316c1c9"
  [proj]="proj-06b0cf9e684f,proj-082e3620a0bb,proj-1ddd02a36695,proj-210490c1df4f,proj-26c69d9d4768"
  [black]="black-00975fca8369,black-0790cdc9bdfd,black-330457f79d99,black-35fa17d21b3d,black-384c66e4283c"
  [rxjava]="rxjava-006d701fb399,rxjava-1c8f5821ed8a,rxjava-32868fd52d7a,rxjava-354214272a97,rxjava-3f173c488095"
  [fsharp]="fsharp-03e44273bd52,fsharp-1976ed2cc84e,fsharp-20451b4caa9e,fsharp-2440fe1cc776,fsharp-270432d5ccf8"
  [syn]="syn-0a8094935f16,syn-45ff4d411dd2,syn-4b41f6875e55,syn-571fcd720ae7,syn-5c8207c9e9c7"
)
PATCH=$ROOT/patches/${AGENT}__${REPO}.diff
OUT=$ROOT/results/jobs-${AGENT}-${REPO}
TASK=$ROOT/tasks/swe-sweep__${REPO}
cd "$SWEEP"
uv run sweep eval "$TASK" "$PATCH" --bugs "${BUGS[$REPO]}" -o "$OUT" --timeout 7200
echo "eval-$AGENT-$REPO exit=$?" >> "$ROOT/results/evals.log"
