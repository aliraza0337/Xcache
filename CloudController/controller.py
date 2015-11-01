import thread
import zlib
import hashlib
import difflib
import time
import socket
import cPickle
import random
import string
import os
import diff_match_patch
import datetime
import sys
import edgeCacheObject
from preFetching import ALL_WEBSITES

global FROM_INTERNET, PUSH_TO_EDGE_CACHE, REQUEST_REFRER, WEB_PAGE_CHANGE_TRACK
REQUEST_REFRER = {}
WEB_PAGE_CHANGE_TRACK = {}
FROM_INTERNET = []
PUSH_TO_EDGE_CACHE = []
BW = 100

def startController():
	thread.start_new_thread( process_FromInternet, (1,))
	#thread.start_new_thread( sendToEdgeCache, (1,))

def createObject(objectReceived):
	FROM_INTERNET.append(objectReceived)

class MemoryObject:
	def __init__(self, url, ash, obj):
		self.url = url
		self.hash = ash
		self.obj = obj

class WebPage:
	def __init__ (self, Nreq):
		self.objects = {}
		self.N = Nreq



class HTTPObject:
	def __init__(self, headers, url, content, status, reason, request_ver, refrer, RTT ):
		self.request_ver = request_ver
		self.headers = headers
		self.url = url
		self.content = content
		self.status = status
		self.reason = reason
		self.refrer = refrer
		self.location = ''
		self.webpage = ''
		self.canApplyDiff = False
		self.maxAge = 0
		self.hash = hashlib.sha224(self.content).hexdigest()
		self.getHeaderValues()
		
		
		# web object attributes for Utility calculation
		self.timeToChange = []
		self.expirationTime = time.time() + float(self.maxAge)
		self.lastChangeTime = time.time()
		self.RTT = RTT
		self.size = len(content)

		self.getWebPage() # to keep track of the object & related website



	def getHeaderValues(self):
		for h in self.headers:
			if h[0] == 'cache-control' or h[0] == 'Cache-Control': #gets Max-age 
				tok = h[1].split(',')
				for t in tok:
					if 'max-age' in t:
						self.maxAge = t.split('=')[1]
			#get weather objects is text or not to apply diff 
			if (h[0] == 'content-type' and 'text' in h[1]) or (h[0] == 'Content-Type' and 'text' in h[1]): 
				self.canApplyDiff = True

			if h[0] == 'location' or h[0] == 'Location': #for redirections 
				self.location=  h[1]

	def getWebPage(self):
		global REQUEST_REFRER
		
		if self.status == 302:
			string = self.location
			REQUEST_REFRER[string] = self.url
			REQUEST_REFRER[self.url] = ''
		
		if not (self.url in REQUEST_REFRER):
			REQUEST_REFRER[self.url] = self.refrer
		
		if self.refrer == '':
			thisURL = self.url
		else:
			thisURL = self.refrer
		
		while 1:
			if thisURL in REQUEST_REFRER:
				previous = thisURL
				thisURL = REQUEST_REFRER[thisURL]
				if thisURL == '':
					self.webpage = previous
					return
			else:
				break
			
	def prepareObject(self):
		res = '%s %s %s\r\n' % (self.request_ver, self.status, self.reason)
		for header in self.headers:
			res += header[0] + ": " + header[1] +"\n"
		res = res+"\r\n"+self.content
		return res
	
	def isX1 (self):


		return True # if the change time > T
		return False # if the change time < T
	
	def addTimeStamp(self, t):
		self.timeToChange.append( t - self.lastChangeTime)
		self.lastChangeTime = t
		self.timeToChange.sort()


	def copyObject(self, obj):
		self.request_ver = obj.request_ver
		self.headers = obj.headers
		self.content = obj.content
		self.status = obj.status
		self.reason = obj.reason
		self.maxAge = obj.maxAge
		self.hash = obj.hash
		self.expirationTime = time.time() + float(self.maxAge)
		self.lastChangeTime = time.time()
		self.size = len(self.content)
	
	def calculateP(self):

		currentTime = time.time()
		time_elapsed = currentTime - self.lastChangeTime
		counter = 0 
		
		for a in self.timeToChange:
			if time_elapsed > a:
				counter = counter + 1

		if counter == 0:
			return 0.0001
		else:
			return float (counter/len(newArray))

	def calculateUtilities(self):
		global ALL_WEBSITES, BW

		N_req = ALL_WEBSITES[self.webpage].N
		bandwidth = BW
		q = 0  
		if self.lastChangeTime < self.expirationTime:
			q = 1 
		p = float(self.calculateP())
		#
		delta = 1
		n_t = N_req * q * (self.RTT + p*(self.size/BW))
		n_b = N_req * q * p * self.size

		if self.isX1():
			timeBased = (p*delta*self.size)/BW
			print ('here', timeBased, p, delta, self.size, BW) 
			bandwidthBased = (p*delta*self.size)
			print bandwidthBased
		else:
			timeBased = n_t
			bandwidthBased = n_b

		return n_t, timeBased, n_b, bandwidthBased


def process_FromInternet(number):
	global FROM_INTERNET, ALL_WEBSITES

	while 1:
		if len(FROM_INTERNET) != 0:
			tempObj = FROM_INTERNET.pop(0)

			if tempObj.webpage in ALL_WEBSITES: 
			# the object is part of a webpage that we know
				if tempObj.url in ALL_WEBSITES[tempObj.webpage].objects: 
				# the object is a one that we have seen before
					if tempObj.hash != ALL_WEBSITES[tempObj.webpage].objects[tempObj.url].hash: 
					# the hash of the object has changed, we need to update the object
						processObject(tempObj, ALL_WEBSITES[tempObj.webpage].objects[tempObj.url])
					else:
						del tempObj 
						# the object has not changed nothing to be done, we delete this object

				else: 
				# object is a new one we need to add it to the list of the objects
					# added the new object to the list of sites
					ALL_WEBSITES[tempObj.webpage].objects[tempObj.url]=tempObj 
					PUSH_TO_EDGE_CACHE.append(edgeCacheObject.EdgeObject(tempObj.headers, 
											    tempObj.url, 
											    tempObj.content, 
												tempObj.status,
												tempObj.reason, 
												tempObj.request_ver, 
												False) )
			else:
				pass
				#print ("(controller error): an object came with an unknown website ")
				#but still we can send this to edge cache
				PUSH_TO_EDGE_CACHE.append(edgeCacheObject.EdgeObject(tempObj.headers, 
																	tempObj.url, 
																	tempObj.content, 
																	tempObj.status, 
																	tempObj.reason, 
																	tempObj.request_ver, 
																	False) )

def processObject(currentObject, previousObject):
	currentTime = time.time()
	
	if currentObject.canApplyDiff and previousObject.canApplyDiff:
		object_to_send = calculateDiff(currentObject, previousObject) # calculate Diff
	else:
		object_to_send = edgeCacheObject.EdgeObject(currentObject.headers, 
													currentObject.url, 
													currentObject.content, 
													currentObject.status,
													currentObject.reason, 
													currentObject.request_ver, 
													False)
	PUSH_TO_EDGE_CACHE.append(object_to_send)
	previousObject.addTimeStamp(currentTime)
	previousObject.copyObject(currentObject)
	




def calculateDiff(new , old):
	old_content = old.content.decode('utf-8')
	new_content = new.content.decode('utf-8')
	var = diff_match_patch.diff_match_patch()
	diff = var.diff_main(old_content, new_content ,  True)
	
	if len(diff) > 2:
		var.diff_cleanupSemantic(diff)
	
	patch_list = var.patch_make(old_content, new_content, diff)
	patch_text = var.patch_toText(patch_list)  # calculate diff
	#make EdgeCacheObject with content being diff and diff variable as True
	newO = edgeCacheObject.EdgeObject(	new.headers,  
										new.url, 
										patch_text, 
										new.status,
										new.reason, 
										new.request_ver, 
										True)
	return newO




def sendToEdgeCache(number):
	global PUSH_TO_EDGE_CACHE
	EdgeCache_IP = '127.0.0.1' # '195.229.110.139'
	EdgeCache_PORT = 60002
	while True:
		if len(PUSH_TO_EDGE_CACHE) > 0:
			print 'sending ... '
			edgeObject = PUSH_TO_EDGE_CACHE.pop(0)
			MESSAGE = cPickle.dumps(edgeObject)
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((EdgeCache_IP, EdgeCache_PORT))
			s.sendall(MESSAGE)
			s.close()
			del s
		time.sleep(0.010)
