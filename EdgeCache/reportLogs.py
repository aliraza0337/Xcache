import os 
import sys
import glob 
import time
import socket
import cPickle 
	#grep_exp = 'GET http://[a-zA-Z.-]+/[[:blank:]] '
	#os.system('grep -oE '+ grep_exp+path_to_log+'> logs/check.txt'







def getLogs(previous):
	
	finalList = []
	information = {}
	threshHold = 15
	destinationFolder = 'logs/'
	logsDir = '/opt/ats/var/log/trafficserver/squid.log_ham*'
	allFiles = glob.glob(logsDir)
	sorted_allFiles =  sorted(allFiles)
	one = sorted_allFiles[-1]
	print one 
	if one == previous:
		return [],""
	path_to_log = one
	FILE = open(path_to_log)
	lines = FILE.readlines()

	for line in lines: 

		tokens = line.split(' ')
		time = tokens[0]
		user = tokens[2]
		url = tokens[6]
		
		if user in information:
			information[user].append([time, url])
		
		else:
			information[user] = [[time, url]]

	for user in information.keys():
		listOfURLs = information[user]
		prev = listOfURLs[0][0]

		for eachURL in listOfURLs:
			number = float(eachURL[0]) - float(prev)
			if number > threshHold or number == 0:
				lastToken = eachURL[1].split('.')[-1]
				flag = ('jpg' in lastToken) or ('js' in lastToken) or ('png' in lastToken) or ('?' in eachURL[1]) or (';' in eachURL[1])
				print flag
				if not flag:
					finalList.append(eachURL[1])
			prev = eachURL[0]


	return list(set(finalList)) , one 

def sendToController(websites):
	print 'sending Logs'
	print websites
	CONTROLLER_IP = '10.225.3.124'
	CONTROLLER_PORT = 7007
	
	MESSAGE = cPickle.dumps(websites)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((CONTROLLER_IP, CONTROLLER_PORT))
	s.sendall(MESSAGE)
	s.close()
	del s
	time.sleep(0.010)
	return 


def startFunc(num):
	print 'sending LOGS asassa'
	previous = " "
	while 1:
		time.sleep(6)
		print 'passed'
		websites, previous = getLogs(previous)
		if len(websites) > 0:
			sendToController(websites)
#startFunc(1)
