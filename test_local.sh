#!/usr/bin/env bash


kill -9 $(lsof -ti :8080)
sleep 1
python -m http.server 8080 &
sleep 1
open -a "Google Chrome" http://localhost:8080/site
