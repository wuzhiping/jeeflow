#!/bin/bash
set -e

N=$(sudo git log --format='%s' | awk '
    /^ToT fix batch [0-9]+$/ {
        match($0, /[0-9]+$/)
        print substr($0, RSTART, RLENGTH)
        exit
    }
')

N=$(( ${N:-0} + 1 ))

echo "==> ToT fix batch $N"

sudo git add .
sudo git commit -m "ToT fix batch $N"