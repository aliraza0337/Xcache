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
import logging
import edgeCacheObject
import constants
from preFetching import ALL_WEBSITES
global FROM_INTERNET, PUSH_TO_EDGE_CACHE, REQUEST_REFRER, WEB_PAGE_CHANGE_TRACK
REQUEST_REFRER = {}
WEB_PAGE_CHANGE_TRACK = {}
FROM_INTERNET = []
PUSH_TO_EDGE_CACHE = []
BW = constants.BW


logger_3 = logging.getLogger('simple_logger_3')
logger_3.setLevel(logging.INFO)
hdlr_3 = logging.FileHandler('objectsanddiffs.log')
logger_3.addHandler(hdlr_3)




def startController():
	thread.start_new_thread( process_FromInternet, (1,))
	thread.start_new_thread( sendToEdgeCache, (1,))

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
	def __init__(self, headers, url, content, status, reason, request_ver, webpage, phase, RTT ):
		self.request_ver = request_ver
		self.headers = headers
		self.url = url
		self.content = content
		self.status = status
		self.reason = reason
		self.webpage = webpage
		self.phase = phase
		self.canApplyDiff = False
		self.maxAge = 0
		self.hash = hashlib.sha224(self.content).hexdigest()
		self.getHeaderValues()

		# web object attributes for Utility calculation
		self.delta = [] 
		self.timeToChange = []
		#print self.maxAge 
		self.expirationTime = time.time() + float(self.maxAge)
		self.lastChangeTime = time.time()
		self.RTT = RTT
		self.size = len(content)*8


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

	def prepareObject(self):
		res = '%s %s %s\r\n' % (self.request_ver, self.status, self.reason)
		for header in self.headers:
			res += header[0] + ": " + header[1] +"\n"
		res = res+"\r\n"+self.content
		return res

	def isX1 (self):
		l_sum = sum(self.timeToChange)
		l = len(self.timeToChange)
		if l != 0:
			ave_time = l_sum/float(l)
		else:
			return False 
		

		if ave_time < constants.INTERVAL_PREFETCHING:
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
		self.size = len(self.content)*8

	def calculateP(self):

		currentTime = time.time()
		time_elapsed = currentTime - self.lastChangeTime
		counter = 0

		for a in self.timeToChange:
			if time_elapsed > a:
				counter = counter + 1

		if counter == 0:
			return 0.0
		else:	
			l = len(self.timeToChange)
			res =  counter/float(l)
			return res

	def calculateUtilities(self):
		global ALL_WEBSITES, BW

		N_req = ALL_WEBSITES[self.webpage].N
		bandwidth = BW
		q = 0

		if time.time() > self.expirationTime:
			q = 1

		p = float(self.calculateP())

		if len(self.delta) == 0:
			delta_value = self.size
		else:	
			delta_value = sum(self.delta)/float(len(self.delta))

		n_t = N_req * q * (self.RTT + p*( self.size/float(BW) ) )
		n_b = N_req*q*p*self.size
		x1orx2 = 'x2'
		
		if self.isX1():
			x1orx2 = 'x1'
			timeBased = (p*delta_value)/float(BW)
			bandwidthBased = p*delta_value
		else:
			timeBased = n_t
			bandwidthBased = n_b

		logstring = ('n_req, q, rtt, p, size, delta', N_req, q, self.RTT, p , self.size, delta_value, x1orx2)
		return n_t, timeBased, n_b, bandwidthBased , logstring




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
						#print 'Object Changed'
					# the hash of the object has changed, we need to update the object
						try:
							processObject(tempObj, ALL_WEBSITES[tempObj.webpage].objects[tempObj.url])
						except:
							pass
					else:
						del tempObj
						# the object has not changed nothing to be done, we delete this object

				else:
				# object is a new one we need to add it to the list of the objects
					# added the new object to the list of sites
					ALL_WEBSITES[tempObj.webpage].objects[tempObj.url]=tempObj

					log_string = 'OBJECT: '+tempObj.phase+':'+tempObj.webpage+':'+str(len(tempObj.content))
					logger_3.info(log_string)
					
					PUSH_TO_EDGE_CACHE.append(edgeCacheObject.EdgeObject(tempObj.headers,
											    tempObj.url,
											    tempObj.content,
												tempObj.status,
												tempObj.reason,
												tempObj.request_ver,
												False, 
												tempObj.webpage, 
												tempObj.canApplyDiff) )
			else:
				#but still we can send this to edge cache
				log_string = 'OBJECT: '+tempObj.phase+':'+tempObj.webpage+':'+str(len(tempObj.content))
				logger_3.info(log_string)
				PUSH_TO_EDGE_CACHE.append(edgeCacheObject.EdgeObject(tempObj.headers,
																	tempObj.url,
																	tempObj.content,
																	tempObj.status,
																	tempObj.reason,
																	tempObj.request_ver,
																	False, 
																	tempObj.webpage, 
																	tempObj.canApplyDiff) )

def processObject(currentObject, previousObject):
	currentTime = time.time()

	if currentObject.canApplyDiff and previousObject.canApplyDiff:
		try:
			object_to_send = calculateDiff(currentObject, previousObject) # calculate Diff
			
		except:
			logger_3.info('Could not calculate diff -- ' + currentObject.url)
			return
			pass
	else:
		object_to_send = edgeCacheObject.EdgeObject(currentObject.headers,
													currentObject.url,
													currentObject.content,
													currentObject.status,
													currentObject.reason,
													currentObject.request_ver,
													False, 
													currentObject.webpage, 
													currentObject.canApplyDiff)
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
	log_string = 'OBJECT_DIFF:'+new.phase+':'+new.webpage+':'+str(len(old_content)) +' :'+ str(len(patch_text))
	logger_3.info(log_string)
	# to keep track of deltas
	old.delta.append( len(patch_text)*8 )
	newO = edgeCacheObject.EdgeObject(	new.headers,
										new.url,
										patch_text,
										new.status,
										new.reason,
										new.request_ver,
										True,
										new.webpage, 
										new.canApplyDiff)
	return newO




def sendToEdgeCache(number):
	global PUSH_TO_EDGE_CACHE
	EdgeCache_IP = constants.EDGECACHE_IP # '195.229.110.139'
	EdgeCache_PORT = constants.EDGECACHE_PORT_OBJECTS
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((EdgeCache_IP, EdgeCache_PORT))

	while True:
		
		if len(PUSH_TO_EDGE_CACHE) > 0:
			
			edgeObject = PUSH_TO_EDGE_CACHE.pop(0)
			#print edgeObject.url
			MESSAGE = cPickle.dumps(edgeObject)
			try:
				#print MESSAGE
				#print '---------'
				s.sendall(MESSAGE)
				s.sendall('EDGEALIRAZAOBJECT')
			except:
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.connect((EdgeCache_IP, EdgeCache_PORT))	
		#time.sleep(0.001)
