import time
import thread
import copy

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.proxy import *
import selenium.webdriver.firefox.webdriver as fwb
import socket as dummysocket
import cPickle
import Queue as Q
import controller
global ALL_WEBSITES, PREFETCHING_QUEUE
PREFETCHING_QUEUE = Q.PriorityQueue()

maxBootstrap = 30
bootstrapSites = {}
ALL_WEBSITES = {}

def openPage (webpage):

	myProxy = "127.0.0.1:9999"
	proxy = Proxy ({
		'proxyType':ProxyType.MANUAL,
		'httpProxy': myProxy,
		'ftpProxy': myProxy,
		'sslProxy': myProxy,
		'noProxy': ''
		})

	binary = fwb.FirefoxBinary(firefox_path='/usr/bin/firefox')
	profile = webdriver.FirefoxProfile()
	profile.set_preference('datareporting.healthreport.uploadEnabled', False)
	profile.set_preference('datareporting.healthreport.service.enabled', False)
	profile.set_preference('datareporting.healthreport.service.firstRun', False)
	profile.set_preference('app.update.auto', False)
	profile.set_preference('app.update.enabled', False)
	profile.set_preference('browser.cache.disk.enable', False)
	profile.set_preference('browser.cache.memory.enable', False)
	profile.set_preference('browser.cache.offline.enable', False)
	profile.set_preference('network.http.use-cache', False)
	profile.set_preference('network.dns.disablePrefetch', True)
	profile.set_preference('network.http.accept-encoding', '')
	profile.update_preferences()

	browser = webdriver.Firefox(firefox_profile=profile, firefox_binary=binary, proxy=proxy)
	browser.implicitly_wait(50)
	browser.set_page_load_timeout(100)

	browser.set_window_size(1920, 1080)
	browser.get (webpage)
	while browser.title == "Problem loading page":
		browser.get (webpage)
		time.sleep(0.001)

	del profile
	print "-- Finished loading ", browser.title
	browser.quit()
	del browser



def bootstrap(a):
	global bootstrapSites
	print "bootstraping thread started"

	while True:
		if len (bootstrapSites) > 0:

			for item in bootstrapSites:
				if bootstrapSites[item][1] <= time.time():
					display = Display(visible=0, size=(1920,1080))
					display.start()
					openPage(item)
					bootstrapSites[item][0]-=1
					bootstrapSites[item][1]=time.time()+20

					if bootstrapSites[item][0] <=0 :
						del bootstrapSites[item]

						# TODO:
						# add it to the prefetching queue

					display.stop()
		time.sleep(1)




def sitesPrefetching (number):

	global PREFETCHING_QUEUE
	newPriority = 0 
	while True:
		display = Display(visible=0, size=(1920,1080))
		display.start()
		currentTime = time.time()
		a = PREFETCHING_QUEUE.get()
		
		if a[0] < currentTime+10: 
			openPage(a[1])
			display.stop()
		else:
			PREFETCHING_QUEUE.put((newPriority, webpage))







def receiveLogs(num):
	global ALL_WEBSITES

	tmp = [('http://www.cnn.com/', 10)]

	for siteInfo in tmp:
		if siteInfo[0] in ALL_WEBSITES:
			ALL_WEBSITES[siteInfo[0]].N = 0.7*ALL_WEBSITES[siteInfo[0]].N + 0.3*siteInfo[1] # TODO: fix the ewma alpha parameter (at the moment random number is given)
		else:
			bootstrapSites[siteInfo[0]]=[maxBootstrap, 0]
			ALL_WEBSITES[siteInfo[0]]=controller.WebPage(siteInfo[1])

	return



	# CONTROLLER_IP = '10.225.3.124'
	# CONTROLLER_PORT = 7007

	# s = dummysocket.socket(dummysocket.AF_INET, dummysocket.SOCK_STREAM)
	# s.setsockopt(dummysocket.SOL_SOCKET, dummysocket.SO_REUSEADDR, 1)

	# s.bind((CONTROLLER_IP, CONTROLLER_PORT))

	# while 1:

	# 	s.listen(1)
	# 	conn, addr = s.accept()
	# 	MESSAGE= ""
	# 	data = conn.recv(1024)

	# 	while data:
	# 		MESSAGE += data
	# 		data = conn.recv(1024)

	# 	websites = cPickle.loads(MESSAGE)

	# 	for web in websites:
	# 		if not (web in ALL_WEBSITES):
	# 			ALL_WEBSITES[web] = ''
	# 			PREFETCHING_QUEUE.put(( time.time() + 1800 ,web))
