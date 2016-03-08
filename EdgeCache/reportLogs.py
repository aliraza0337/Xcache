import os 
import sys
import glob 
import time
import socket
import cPickle
import constants

def getLogs(previous):	
	finalList = []
	information = {}
	popularity = {}
	threshHold = 15
	logsDir = constants.LOG_DIR
	allFiles = glob.glob(logsDir)
	sorted_allFiles =  sorted(allFiles)
	if len(sorted_allFiles)< 1:
		return [], " "

	one = sorted_allFiles[-1]
	print one 
	if one == previous:
		return [],one
	path_to_log = one
	FILE = open(path_to_log)
	lines = FILE.readlines()
 	dictionary_referrer = {}
	dictionary_url = {}
 	for line in lines:
 		tokens = line.split(' ')
 		lastToken = tokens[10].split('.')[-1]
 		flag = ('swf' in lastToken) or ('jpg' in lastToken) or ('js' in lastToken) or ('png' in lastToken) or ('svg' in lastToken) or ('css' in lastToken) or ('gif' in lastToken) or ('woff' in lastToken) or ('ico' in lastToken)
 		if tokens[6] in dictionary_url:
			dictionary_url[tokens[6]] += 1
		else:
			dictionary_url[tokens[6]] = 1

		if flag or tokens[10]=='-\n' or '?' in tokens[10]:
			continue

 		if tokens[10].strip() in dictionary_referrer:
			dictionary_referrer[tokens[10].strip()] += 1
		else:
			dictionary_referrer[tokens[10].strip()] = 1
	for d in dictionary_referrer:
		if dictionary_referrer[d] > 10 and d in dictionary_url:
			finalList.append([ d, dictionary_url[d] ]) 
	return finalList , one 


def sendToController(websites):

	CONTROLLER_IP = constants.CONTROLLER_IP
	CONTROLLER_PORT = constants.CONTROLLER_PORT_LOGS
	MESSAGE = cPickle.dumps(websites)
	while 1:
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((CONTROLLER_IP, CONTROLLER_PORT))
			s.sendall(MESSAGE)
			s.close()
			del s
			break
		except:
			print 'Trying to send logs\n'
			time.sleep(100)
			
	return 


def startFunc(num):
	print 'Sending Logs!'
	previous = " "
	time.sleep(10)
	while 1:
		try:
			websites, previous = getLogs(previous)
			print websites
			if len(websites) > 0:
				try:
					sendToController(websites)
				except:
					pass
			time.sleep(1800)
		except:
			pass
