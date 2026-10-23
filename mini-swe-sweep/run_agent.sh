#!/bin/bash
# mini-swe-sweep agent runner: run one agent on one repo clone, capture diff.
# usage: run_agent.sh <agent: claude|amp> <repo: libexpat|click|gson|roslyn|z3|tokio>
set -u
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"
ROOT=/home/danie/mini-swe-sweep
AGENT=$1
REPO=$2
declare -A REF=( [libexpat]=R_2_4_3 [click]=8.0.1 [gson]=gson-parent-2.8.0 [roslyn]=NET-SDK-10.0.100 [z3]=z3-4.16.0 [tokio]=tokio-1.33.0 [hdf5]=hdf5-1_10_8 [proj]=6.3.0 [black]=23.3.0 [rxjava]=v2.2.5 [fsharp]=15b5a6ce4bf34c03ef172e1e01eedd7e039cc5c4 [syn]=1.0.36 )
declare -A URL=( [libexpat]=https://github.com/libexpat/libexpat.git [click]=https://github.com/pallets/click.git [gson]=https://github.com/google/gson.git [roslyn]=https://github.com/dotnet/roslyn.git [z3]=https://github.com/Z3Prover/z3.git [tokio]=https://github.com/tokio-rs/tokio.git [hdf5]=https://github.com/HDFGroup/hdf5.git [proj]=https://github.com/OSGeo/PROJ.git [black]=https://github.com/psf/black.git [rxjava]=https://github.com/reactivex/rxjava.git [fsharp]=https://github.com/dotnet/fsharp.git [syn]=https://github.com/dtolnay/syn.git )
CAP_SECONDS=${CAP_SECONDS:-3600}

D=$ROOT/repos/$REPO
if [ ! -d "$D/.git" ]; then
  rm -rf "$D"
  if ! git clone --quiet --depth 1 --branch "${REF[$REPO]}" "${URL[$REPO]}" "$D" 2>/dev/null; then
    # base_ref may be a commit SHA, which --branch cannot clone; fetch it directly
    git init --quiet "$D" \
      && git -C "$D" remote add origin "${URL[$REPO]}" \
      && git -C "$D" fetch --quiet --depth 1 origin "${REF[$REPO]}" \
      && git -C "$D" checkout --quiet FETCH_HEAD \
      || exit 1
  fi
fi
git -C "$D" checkout --quiet "${REF[$REPO]}" 2>/dev/null || true
git -C "$D" clean -fdxq
git -C "$D" reset --hard --quiet

OUT=$ROOT/patches/${AGENT}__${REPO}.diff
LOG=$ROOT/logs/${AGENT}__${REPO}.log

START=$(date +%s)
case $AGENT in
  claude)
    [ -f "$HOME/.claude_api_key" ] && . "$HOME/.claude_api_key"
    timeout --kill-after=60 $CAP_SECONDS bash -c \
      "cd '$D' && claude -p --model claude-opus-5-5 --dangerously-skip-permissions < '$ROOT/prompt.md'" >"$LOG" 2>&1
    ;;
  amp)
    timeout --kill-after=60 $CAP_SECONDS bash -c \
      "cd '$D' && amp -m claude-opus-5-5 -x < '$ROOT/prompt.md'" >"$LOG" 2>&1
    ;;
  *) echo "unknown agent $AGENT"; exit 1;;
esac
STATUS=$?

git -C "$D" add -A
git -C "$D" diff --cached --binary > "$OUT"
END=$(date +%s)
echo "[$AGENT/$REPO] exit=$STATUS duration=$((END-START))s diff_lines=$(wc -l < "$OUT") $(date)" | tee -a "$ROOT/logs/sessions.log"
