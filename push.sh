#!/bin/bash
set -e

N=$(sudo git log --format='%s' | awk '
    /^sla fix batch [0-9]+$/ {
        match($0, /[0-9]+$/)
        print substr($0, RSTART, RLENGTH)
        exit
    }
')

N=$(( ${N:-0} + 1 ))

echo "==> sla fix batch $N"

sudo git add .
sudo git commit -m "sla fix batch $N"
sudo git push