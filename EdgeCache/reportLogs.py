import os 
import sys
import glob 
import time
import socket
import cPickle
import constants  
	#grep_exp = 'GET http://[a-zA-Z.-]+/[[:blank:]] '
	#os.system('grep -oE '+ grep_exp+path_to_log+'> logs/check.txt'

def getLogs(previous):
	
	finalList = []
	information = {}
	popularity = {}
	threshHold = 15
	destinationFolder = 'logs/'
	logsDir = constants.LOG_DIR
	allFiles = glob.glob(logsDir)
	sorted_allFiles =  sorted(allFiles)
	#print sorted_allFiles

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

	#print dictionary_url
	for d in dictionary_referrer:
		if dictionary_referrer[d] > 10 and d in dictionary_url:
			finalList.append([ d, dictionary_url[d] ]) 
 	#print finalList
	# 	tokens = line.split(' ')
	# 	time = tokens[0]
	# 	user = tokens[2]
	# 	url = tokens[6]
		
	# 	if url in popularity:
	# 		popularity[url] += 1
	# 	else: 
	# 		popularity[url] = 1 

	# 	if user in information:
	# 		information[user].append([time, url])
		
	# 	else:
	# 		information[user] = [[time, url]]

	# for user in information.keys():
	# 	listOfURLs = information[user]
	# 	prev = listOfURLs[0][0]

	# 	for eachURL in listOfURLs:
	# 		number = float(eachURL[0]) - float(prev)
	# 		if number > threshHold or number == 0:
	# 			lastToken = eachURL[1].split('.')[-1]
	# 			flag =  ('jpg' in lastToken) or ('js' in lastToken) or ('png' in lastToken) or ('?' in eachURL[1]) or (';' in eachURL[1]) or ('svg' in lastToken) or ('css' in lastToken) or ('gif' in lastToken) or ('woff' in lastToken) or ('ico' in lastToken)


	# 			if not flag:
	# 				t = eachURL[1].split(':')
	# 				#print t
	# 				if len( t ) > 2:
	# 					u = t[0]+':'+t[1]+'/'
	# 					finalList.append([u, popularity[eachURL[1]]])
	# 				elif len(t)==2 and 'http' in t[0]:
	# 					finalList.append([eachURL[1], popularity[eachURL[1]]])
	# 				elif len(t)==1:
	# 					finalList.append([t[0], popularity[eachURL[1]]])
	# 				else:
	# 					finalList.append(['http://www.'+t[0], popularity[eachURL[1]]])

	# 		prev = eachURL[0]

	#print finalList
	#list(set(finalList))
	return finalList , one 

def sendToController(websites):
	#print websites
	CONTROLLER_IP = constants.CONTROLLER_IP
	CONTROLLER_PORT = constants.CONTROLLER_PORT_LOGS
	MESSAGE = cPickle.dumps(websites)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((CONTROLLER_IP, CONTROLLER_PORT))
	s.sendall(MESSAGE)
	s.close()
	del s
	time.sleep(0.010)
	return 


def startFunc(num):
	print 'Sending Logs!'
	previous = " "
	#websites, previous = getLogs(previous)
	#print websites
	time.sleep(100)
	while 1:
		try:
			websites, previous = getLogs(previous)
			print websites
			#break
			if len(websites) > 0:
				try:
					sendToController(websites)
				except:
					pass
			time.sleep(1800)
		except:
			pass
#startFunc(1)
