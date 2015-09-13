import thread
import zlib
import hashlib
import difflib
import time
import socket
import datetime
import cPickle
import random
import string
import datetime
global writeToDiskMem, fromInternet, ObjectsOnMem, edgeCache

writeToDiskMem = []
fromInternet = []
edgeCache = []
ObjectsOnMem = {}



class HTTPObject:
	def __init__(self, headers, url, content, status, reason ):
		self.headers = headers
		self.url = url
		self.content = content
		self.isText = False
		self.hash = 0
		self.status = status
		self.maxAge = 0
		self.fileName = ""
		self.reason = reason