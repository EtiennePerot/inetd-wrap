#!/usr/bin/env python3

import os, sys, threading, subprocess, optparse, time, socket, select, signal

parser = optparse.OptionParser(usage='Usage: %prog -p port [options] /usr/bin/foo-serverd')
parser.add_option('-p', '--port', dest='port', type='int', help='The port number that the subprocess will be listening on.', metavar='PORT')
parser.add_option('-d', '--destination', dest='host', help='The destination hostname that the subprocess will be listening on. (Default: localhost)', default='localhost', metavar='HOSTNAME')
parser.add_option('-k', '--kill-timeout', dest='timeout', type='int', help='The timeout after which the connection will be closed if no data has been passed in either direction. (Default: 10 seconds)', default=10, metavar='TIMEOUT')
parser.add_option('-t', '--time-delay', dest='delay', type='int', help='The time it will take for the subprocess before it starts actually listening. Data will be buffered until this amount of time. (Default: 3 seconds)', default=3, metavar='DELAY')
(option, args) = parser.parse_args()

if option.port is None:
	print('The port number must be provided.', file=sys.stderr)
	parser.print_usage(file=sys.stderr)
	sys.exit(1)
if len(args) != 1:
	print('Must provide a command to run.', file=sys.stderr)
	parser.print_usage(file=sys.stderr)
	sys.exit(1)

sys.stdin = sys.stdin.detach()
sys.stdout = sys.stdout.detach()

class ProcessThread(threading.Thread):
	def __init__(self, processConnection, timeout):
		self.processConnection = processConnection
		self.timeout = timeout
		threading.Thread.__init__(self)
		self.daemon = True
		self.start()
	def updateTimeout(self, data):
		if len(data):
			self.timeout.set(time.time())
		return data

class InetdToProcessThread(ProcessThread):
	def run(self):
		while True:
			self.processConnection.sendall(self.updateTimeout(sys.stdin.read(1)))

class ProcessToInetdThread(ProcessThread):
	def run(self):
		while True:
			sys.stdout.write(self.updateTimeout(self.processConnection.recv(1)))
			sys.stdout.flush()

process = subprocess.Popen(
	args,
	stdin = subprocess.PIPE,
	stdout = subprocess.PIPE,
	preexec_fn = os.setsid
)

class ProcessStdoutConsumer(ProcessThread):
	def run(self):
		while True:
			self.updateTimeout(process.stdout.read(1))

class UnsafeMutableInt(object):
	def __init__(self, value=0):
		self.value = value
	def get(self):
		return self.value
	def set(self, value):
		self.value = value

if option.delay > 0:
	time.sleep(option.delay)
if process.poll() is not None:
	sys.exit(0) # Process ended before we could connect

try:
	processConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	processConnection.connect((option.host, option.port))
	timeout = UnsafeMutableInt(time.time())
	processStdoutThread = ProcessStdoutConsumer(processConnection, timeout)
	inetdToProcessThread = InetdToProcessThread(processConnection, timeout)
	processToInetdThread = ProcessToInetdThread(processConnection, timeout)
	pollList = select.poll()
	# Poll every relevant stream; if any of them has any error, stop everything.
	[pollList.register(s) for s in [sys.stdin, sys.stdout, processConnection, process.stdin, process.stdout]]
	keepGoing = True
	errorCondition = select.POLLERR | select.POLLHUP | select.POLLNVAL
	while keepGoing:
		time.sleep(1)
		eventList = pollList.poll(1)
		for _, status in eventList:
			if status & errorCondition:
				keepGoing = False
				break
		if time.time() - timeout.get() > option.timeout:
			break
	if process.poll() is None: # Process is still alive, we must kill it.
			os.killpg(process.pid, signal.SIGTERM) # Kill the process group
			if process.poll() is None: # Still standing?
				time.sleep(1) # Give it a little time
				if process.poll() is None: # Still standing?
					time.sleep(5) # Last chance
					if process.poll() is None: # Still standing?
						os.killpg(process.pid, signal.SIGKILL)
except:
	try:
		os.killpg(process.pid, signal.SIGKILL)
	except:
		pass
