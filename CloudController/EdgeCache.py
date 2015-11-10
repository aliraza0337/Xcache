import os 
import cPickle
from threading import Thread 
import socket as dummysocket
import time 
import diff_match_patch
import reportLogs 
import edgeCacheObject 
import constants 
global ALL_OBJECTS , PUSH_TO_CACHE, PREVIOUS_OBJECTS 

ALL_OBJECTS = [] 
PUSH_TO_CACHE = []
PREVIOUS_OBJECTS = {}


def startfunc():	
	thread1 = Thread(target = listenFromController, args = (1, ))
	thread1.start()
	thread2 = Thread(target = processObjects, args = (1, ))
	thread2.start()
	#thread3 = Thread(target = reportLogs.startFunc, args = (1, ))
	#thread3.start()


def listenFromController(num):

	EdgeCache_IP = constants.EDGECACHE_IP
	EdgeCache_Port = constants.EDGECACHE_PORT_OBJECTS
	print EdgeCache_Port
	s = dummysocket.socket(dummysocket.AF_INET, dummysocket.SOCK_STREAM)
	s.setsockopt(dummysocket.SOL_SOCKET, dummysocket.SO_REUSEADDR, 1)
	s.bind((EdgeCache_IP, EdgeCache_Port))

	print 'Listening ....'
	while 1:
		s.listen(1)
		conn, addr = s.accept()
		MESSAGE= ""
		data = conn.recv(1024)
		while data:
			MESSAGE += data
			data = conn.recv(1024)
		edgeObject = cPickle.loads(MESSAGE)
		print edgeObject.url[:50]
		ALL_OBJECTS.append(edgeObject)
		time.sleep(0.001)



def push_in_cache(edgeObject, mode):
	print 'ready to push    ' + edgeObject.url
	res = '%s %s %s\r\n' % (edgeObject.request_ver, edgeObject.status, edgeObject.reason)
	
	for header in edgeObject.headers:
		res += header[0] + ": " + header[1] +"\n"

	res = res+"\r\n"+edgeObject.content
	with open('cache/Object'+mode+'.txt','wb') as f:
		f.write(res);
	f.close()

	path = 'cache/Object'+mode+'.txt'
	command = 'sudo ./tspush -f cache/Object'+mode+'.txt -u http://'+constants.APS_IP_PORT+' -s '+edgeObject.url
	os.system(command)
	os.system('rm cache/*')


def applyDiff(obj):

	global PREVIOUS_OBJECTS
	
	if obj.url in PREVIOUS_OBJECTS:
		newObject = PREVIOUS_OBJECTS[obj.url]
	else: 
		print 'Object not found!'

	old_content = newObject.content.decode('utf-8')
	diff = obj.content 

	var = diff_match_patch.diff_match_patch()
	patches = var.patch_fromText(diff)
	results = var.patch_apply(patches, old_content)

	
	newObject.content = results[0].encode('utf-8')
	newObject.headers = obj.headers
	newObject.status = obj.status
	newObject.reason = obj.reason

	del obj
	push_in_cache(newObject, 'diff')



def processObjects(num):	
	global ALL_OBJECTS, PUSH_TO_CACHE, PREVIOUS_OBJECTS

	while 1:

		if len(ALL_OBJECTS) > 0:
			edgeObject = ALL_OBJECTS.pop(0)
			
			if not edgeObject.diff:			
				push_in_cache(edgeObject, 'normal')
				PREVIOUS_OBJECTS[edgeObject.url] = edgeObject
				time.sleep(0.001)
			else:
				applyDiff(edgeObject)
		time.sleep(0.001)


startfunc()
