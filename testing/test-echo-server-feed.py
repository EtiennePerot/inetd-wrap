#!/usr/bin/env python3

import sys, time


def w(s):
	sys.stdout.write(' ' + s + ' ')
	sys.stdout.flush()
	time.sleep(.5)

[w(x) for x in 'Hello there! This is a test message.\n This is a message on another line.\n And here we have the third line.\n'.split(' ')]
