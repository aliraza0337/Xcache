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

global fromInternet, ObjectsOnMem, pushToEdgeCache, REQUEST_REFRER, WEB_PAGE_CHANGE_TRACK 
REQUEST_REFRER = {}
WEB_PAGE_CHANGE_TRACK = {}
fromInternet = []
pushToEdgeCache = []
ObjectsOnMem = {}


def startController():
	thread.start_new_thread(process_FromInternet, (1,))
	thread.start_new_thread(sendToEdgeCache, (1,))

def createObject(objectReceived):
	fromInternet.append(objectReceived)

class MemoryObject:
	def __init__(self, url, ash, obj):
		self.url = url
 		self.hash = ash
 		self.obj = obj


class HTTPObject:
	def __init__(self, headers, url, content, status, reason, request_ver, refrer ):

		self.request_ver = request_ver
		self.headers = headers
		self.url = url
		self.content = content
		self.hash = 0
		self.status = status
		self.reason = reason
		self.refrer = refrer
		self.webpage = ''
		self.diff = False
		self.canApplyDiff = False

		#self.lastModified = self.getLastModifiedHeader()
		self.putRefrerInGlobalList()
		self.findWebsite()
		#print 'THAT:' + self.webpage
		self.computeHash()
		self.diffCheck()


	def findWebsite(self):
		#if self.url == 'http://www.cnn.com/':
			#print 'THIS:' + self.refrer
		if self.refrer == '':
			thisURL = self.url
		else:
			thisURL = self.refrer
		#print self.refrer
		while 1:
			if thisURL in REQUEST_REFRER:
				previous = thisURL
				thisURL = REQUEST_REFRER[thisURL]

				if thisURL == '':
					self.webpage = previous
					#print 'self.refrer: ' + self.url
					#print previous
					return
			else:
				break 
	
	def getLocationHeader(self):
		for h in self.headers:
			if h[0] == 'location':
				return h[1]

	
	def putRefrerInGlobalList(self):
		global REQUEST_REFRER

		if self.status == 302:
			string = self.getLocationHeader()
			REQUEST_REFRER[string] = self.url
			REQUEST_REFRER[self.url] = ''

		if self.url in REQUEST_REFRER:
			return 
		else: 
			REQUEST_REFRER[self.url] = self.refrer
		return 

	def getLastModifiedHeader(self):
		for h in self.headers:
			if h[0] == 'last-modified':
				return h[1]
		return ''

	def diffCheck(self):
		for h in self.headers:
			if h[0] == 'content-type' and 'text' in h[1]:
				self.canApplyDiff = True

	def computeHash(self):
		self.hash = hashlib.sha224(self.content).hexdigest()

	def prepareObject(self):
		res = '%s %s %s\r\n' % (self.request_ver, self.status, self.reason)
		for header in self.headers:
			res += header[0] + ": " + header[1] +"\n"
		res = res+"\r\n"+self.content	
		return res
	
	def isValidToServe(self):
		
		if self.webpage == self.url:
			return False 
		
		timeStamps = WEB_PAGE_CHANGE_TRACK[self.webpage][1][self.url]
		

		if len(timeStamps) == 1:
			return True
		else:
			currentTime = time.time()
			t1 = timeStamps[-1]
			t2 = timeStamps[-2]
			diff1 = t1 - t2 
			diff2 = currentTime - t1 
			
			if diff2 > diff1:
				return True
			else:
				return False 
		return True

def getThePriority(url):


	global WEB_PAGE_CHANGE_TRACK
	if url in WEB_PAGE_CHANGE_TRACK:
		return WEB_PAGE_CHANGE_TRACK[url][0]
	else:
		return 0 
	return 0 


def process_FromInternet(number):
	global fromInternet, ObjectsOnMem
	
	while 1:
		if len(fromInternet) != 0:
			
			tempObj = fromInternet.pop(0)

			if tempObj.url in ObjectsOnMem:
				if ObjectsOnMem[tempObj.url].hash != tempObj.hash:
					processObject(tempObj, ObjectsOnMem[tempObj.url].obj)
			else:
	
				if tempObj.webpage in WEB_PAGE_CHANGE_TRACK:

					WEB_PAGE_CHANGE_TRACK[tempObj.webpage][1][tempObj.url] = [time.time()]
				else:

					WEB_PAGE_CHANGE_TRACK[tempObj.webpage] = [1800, {}]
					WEB_PAGE_CHANGE_TRACK[tempObj.webpage][1][tempObj.url] = [time.time()]
				
				ObjectsOnMem[tempObj.url] = MemoryObject(tempObj.url,tempObj.hash,	tempObj)
				pushToEdgeCache.append(tempObj)





def processObject(currentObject, previousObject):

	global ObjectsOnMem, WEB_PAGE_CHANGE_TRACK

	currentTime = time.time()
	previousTime = WEB_PAGE_CHANGE_TRACK[currentObject.webpage][1][currentObject.url][-1]
	difference = currentTime - previousTime
	WEB_PAGE_CHANGE_TRACK[currentObject.webpage][1][currentObject.url].append(currentTime)
	print difference
	
	if difference < WEB_PAGE_CHANGE_TRACK[currentObject.webpage][0]:
		WEB_PAGE_CHANGE_TRACK[currentObject.webpage][0] = max (difference, 420)


	if previousObject.canApplyDiff:
		diff_object = calculateDiff(currentObject, previousObject) #calculate Diff 
		pushToEdgeCache.append(diff_object)
		ObjectsOnMem[currentObject.url].obj = currentObject
	
	else: 
		pushToEdgeCache.append(currentObject)
		ObjectsOnMem[currentObject.url].obj = currentObject



def calculateDiff(new , old):

	old_content = old.content.decode('utf-8')
	new_content = new.content.decode('utf-8')	
	var = diff_match_patch.diff_match_patch()
	diff = var.diff_main(old_content, new_content ,  True)
	
	if len(diff) > 2:
		var.diff_cleanupSemantic(diff)
	
	patch_list = var.patch_make(old_content, new_content, diff)
	patch_text = var.patch_toText(patch_list)
	newO = HTTPObject(new.headers, new.url, patch_text, new.status, new.reason, new.request_ver, new.refrer)
	newO.diff = True
	return newO




def getThisObject(url):

	if url in ObjectsOnMem:
		return ObjectsOnMem[url].obj
	return None






def sendToEdgeCache(number):
	global pushToEdgeCache
	EdgeCache_IP = '10.230.240.204'
	EdgeCache_PORT = 60002

	while True:
		if len(pushToEdgeCache) > 0:
			edgeObject = pushToEdgeCache.pop(0)
			MESSAGE = cPickle.dumps(edgeObject)
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((EdgeCache_IP, EdgeCache_PORT))
			s.sendall(MESSAGE)
			print "Pushing content"
			s.close()
			del s
		time.sleep(0.010)
