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
import logging
import controller
import constants
global ALL_WEBSITES, PREFETCHING_QUEUE, PREFETCHING_LIST


#formatter = logging.Formatter('%(asctime)s %(message)s')

logger_1 = logging.getLogger('simple_logger')
logger_1.setLevel(logging.INFO)
hdlr_1 = logging.FileHandler('prefetching.log')
#hdlr_1.setFormatter(formatter)
logger_1.addHandler(hdlr_1)

logger_2 = logging.getLogger('simple_logger_2')
logger_2.setLevel(logging.INFO)
hdlr_2 = logging.FileHandler('utilitycalculation.log')
#hdlr_1.setFormatter(formatter)
logger_2.addHandler(hdlr_2)


PREFETCHING_LIST = []
PREFETCHING_QUEUE = Q.PriorityQueue()

MAX_BOOTSTRAP  = constants.MAX_BOOTSTRAP
BOOTSTRAPSITES  = {}
ALL_WEBSITES = {}
TIME =  constants.INTERVAL_PREFETCHING


def startPrefetching(num):
	thread.start_new_thread(receiveLogs, (1,))
	thread.start_new_thread(bootstrap, (1,))
	thread.start_new_thread(sitesPrefetching, (1,))



def openPage (webpage):

	myProxy = "127.0.0.1:9999"
	proxy = Proxy ({
		'proxyType':ProxyType.MANUAL,
		'httpProxy': myProxy,
		'ftpProxy': myProxy,
		'sslProxy': '',
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

	#for modifying header
	profile.add_extension( 'modify_headers-0.7.1.1-fx.xpi')
	profile.set_preference('modifyheaders.headers.count', 1)
	profile.set_preference('modifyheaders.headers.action0', "Add")
	profile.set_preference('modifyheaders.headers.name0', 'webpage')
	profile.set_preference('modifyheaders.headers.value0', webpage)
	profile.set_preference('modifyheaders.headers.enabled0', True)
	profile.set_preference('modifyheaders.config.active', True)
	profile.set_preference('modifyheaders.config.alwaysOn', True)
	#

	profile.update_preferences()

	browser = webdriver.Firefox(firefox_profile=profile, firefox_binary=binary, proxy=proxy)
	browser.implicitly_wait(30)
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
	global BOOTSTRAPSITES
	print "Bootstraping thread started\n"

	while True:
		if len (BOOTSTRAPSITES ) > 0:

			for item in BOOTSTRAPSITES.keys() :

				if BOOTSTRAPSITES [item][1] <= time.time():
					display = Display(visible=0, size=(1920,1080))
					display.start()

					print ('Bootstraping: ', item, 'for: ',BOOTSTRAPSITES[item][0] )

					log_string = 'BOOTSTRAP: '+str(time.time()) +' :'+item
					logger_1.info(log_string)
					try:
						openPage(item)
					except:
						pass
					BOOTSTRAPSITES [item][0]-=1
					BOOTSTRAPSITES [item][1]=time.time()+constants.INTERVAL_BOOTSTRAP
					print BOOTSTRAPSITES [item][1]
					if BOOTSTRAPSITES [item][0] <=0 :
						print 'Added to PREFETCHING_LIST'
						log_string = 'BOOTSTRAP: ADDED_TO_PREFETCHING_LIST: '+item
						logging.info(log_string)
						PREFETCHING_LIST.append(item)

						del BOOTSTRAPSITES[item]
					display.stop()

		time.sleep(1)


def sitesPrefetching (number):
	PREFETCHING_BOOL = False
	while True:

		global PREFETCHING_QUEUE , TIME, PREFETCHING_LIST
		startTime = time.time()
		if len(PREFETCHING_LIST) > 0:
			PREFETCHING_QUEUE = calculateUtilities()
			print PREFETCHING_QUEUE

		while not PREFETCHING_QUEUE.empty():
			PREFETCHING_BOOL = True

			w = PREFETCHING_QUEUE.get()
			display = Display(visible=0, size=(1920,1080))
			display.start()

			log_string = 'PREFETCHING: '+str(time.time()) +' :'+w[1]
			print log_string
			logger_1.info(log_string)
			try:
				openPage(w[1])
			except:
				pass
			display.stop()

			if time.time() - startTime >= TIME:
				break # we have reached the end of the slot for prefetching we should stop and start the next slot

		if PREFETCHING_BOOL:
			if time.time() - startTime < TIME:
				print 'going to sleep:' + str(TIME) +' '+str(time.time() - startTime)
				time.sleep(TIME - (time.time() - startTime))



def receiveLogs(num):

	global ALL_WEBSITES
	CONTROLLER_IP = constants.CONTROLLER_IP
	print CONTROLLER_IP
	CONTROLLER_PORT = constants.CONTROLLER_PORT_LOGS
	s = dummysocket.socket(dummysocket.AF_INET, dummysocket.SOCK_STREAM)
	s.setsockopt(dummysocket.SOL_SOCKET, dummysocket.SO_REUSEADDR, 1)
	s.bind((CONTROLLER_IP, CONTROLLER_PORT))

	while 1:
		s.listen(1)
		conn, addr = s.accept()
		MESSAGE= ""
		data = conn.recv(1024)
		while data:
			MESSAGE += data
			data = conn.recv(1024)
		websites = cPickle.loads(MESSAGE)
		tmp = websites
		print tmp
		for siteInfo in tmp:
			if siteInfo[0] in ALL_WEBSITES:
				ALL_WEBSITES[siteInfo[0]].N = 0.7*ALL_WEBSITES[siteInfo[0]].N + 0.3*siteInfo[1] # TODO: fix the ewma alpha parameter (at the moment random number is given)
			else:
				BOOTSTRAPSITES [siteInfo[0]]=[MAX_BOOTSTRAP , 0]
				ALL_WEBSITES[siteInfo[0]]=controller.WebPage(siteInfo[1])

				log_string = 'ADDED FROM LOGS: '+siteInfo[0]
				logging.info(log_string)

	return


	# tmp = [ ('http://www.cnn.com/', 10), 
	# 	('http://www.bbc.com/', 10),  
	# 	('http://www.espn.com/', 10),  
	# 	('http://www.yahoo.com/', 10),  
	# 	('http://www.microsoft.com/', 10),  
	# 	('http://www.msn.com/', 10),  
	# 	('http://www.youtube.com/', 10),  
	# 	('http://www.booking.com/', 10), 
	# 	('http://www.amazon.com/', 10), 
	# 	('http://www.alibaba.com/', 10), 
	# 	('http://www.nytimes.com/', 10), 
	# 	('http://www.dailymail.com/', 10), 
	# 	('http://www.apple.com/', 10), 
	# 	('http://www.tv.com/', 10), 
	# 	('http://www.tvguide.com/', 10)]
	
	# for siteInfo in tmp:
	# 	if siteInfo[0] in ALL_WEBSITES:
	# 		ALL_WEBSITES[siteInfo[0]].N = 0.7*ALL_WEBSITES[siteInfo[0]].N + 0.3*siteInfo[1] # TODO: fix the ewma alpha parameter (at the moment random number is given)
	# 	else:
	# 		BOOTSTRAPSITES [siteInfo[0]]=[MAX_BOOTSTRAP , 0]
	# 		ALL_WEBSITES[siteInfo[0]]=controller.WebPage(siteInfo[1])
	# 		log_string = 'ADDED FROM LOGS: '+siteInfo[0]
	# 		logger_1.info(log_string)






def calculateUtilities():
	global ALL_WEBSITES, PREFETCHING_QUEUE, PREFETCHING_LIST
	PREFETCHING_QUEUE =  Q.PriorityQueue()
	for webpage in PREFETCHING_LIST:
		print 'calculateUtilities'
		n_t = float(0.000)
		d_t = float(0.000)
		n_b = float(0.000)
		d_b = float(0.000)
		webPageObjects = ALL_WEBSITES[webpage].objects
		logger_2.info('Utility Calculation: ' + webpage)
		for o in webPageObjects.keys():
			x1, x2, x3, x4, st = webPageObjects[o].calculateUtilities()
			print st
			n_t = n_t + x1
			d_t = d_t + x2
			n_b = n_b + x3
			d_b = d_b + x4
			logger_2.info(st)
		
		if d_t == 0:
			d_t = 1
		if d_b == 0:
			d_b = 1

		t = float(float(n_t/d_t) + float(n_b/d_b))
		log_string = 'UTILITY: '+webpage +' :TIME= '+str( n_t/float(d_t) )+':BW='+str( n_b/float(d_b))
		#print log_string
		logger_1.info(log_string)
		logger_2.info(log_string)
		PREFETCHING_QUEUE.put((t, webpage))
	return PREFETCHING_QUEUE



