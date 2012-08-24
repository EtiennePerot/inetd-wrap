#!/usr/bin/env python3

import sys, time

def w(s):
	try:
		sys.stdout.write(s + ' ')
		sys.stdout.flush()
	except:
		sys.exit(0)
	time.sleep(.5)

[w(x) for x in 'Hello there! This is a test message.\n This is a message on another line.\n And here we have the third line.\n Now we try to timeout...'.split(' ')]
time.sleep(15)
[w(x) for x in 'Should have timeouted by now. If that is not the case, there is a problem somewhere.'.split(' ')]
