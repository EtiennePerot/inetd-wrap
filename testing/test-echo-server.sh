#!/usr/bin/env bash

cd "`dirname "$0"`"
./test-echo-server-feed.py | ../inetd-wrap.py -p 1337 ./echo-server.sh
