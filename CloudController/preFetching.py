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



logger_1 = logging.getLogger('simple_logger')
logger_1.setLevel(logging.INFO)
hdlr_1 = logging.FileHandler('prefetching.log')
logger_1.addHandler(hdlr_1)

logger_2 = logging.getLogger('simple_logger')
logger_2.setLevel(logging.INFO)
hdlr_2 = logging.FileHandler('utilitycalculation.log')
logger_2.addHandler(hdlr_2)


PREFETCHING_LIST = []
PREFETCHING_QUEUE = Q.PriorityQueue()


MAX_BOOTSTRAP  = constants.MAX_BOOTSTRAP
BOOTSTRAPSITES  = {}
BOOTSTRAPSITES_COUNTER = 0 
PREFETCHING_COUNTER = 0 
ALL_WEBSITES = {}
TIME =  constants.INTERVAL_PREFETCHING


def startPrefetching(num):
	thread.start_new_thread(receiveLogs, (1,))
	thread.start_new_thread(bootstrap, (1,))
	thread.start_new_thread(sitesPrefetching, (1,))



def openPage (webpage, check):

	global BOOTSTRAPSITES_COUNTER, PREFETCHING_COUNTER
	display = Display(visible=0, size=(1920,1080))
	display.start()

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
	profile.set_preference('modifyheaders.headers.value0', check+':'+webpage)
	profile.set_preference('modifyheaders.headers.enabled0', True)
	profile.set_preference('modifyheaders.config.active', True)
	profile.set_preference('modifyheaders.config.alwaysOn', True)
	#
	profile.update_preferences()
	browser = webdriver.Firefox(firefox_profile=profile, firefox_binary=binary, proxy=proxy)
	browser.set_page_load_timeout(70)
	browser.set_window_size(1920, 1080)
	
	try:
		browser.get(webpage)
		print "-- Finished loading ", browser.title
	except:
		print "-- Problem loading "
		display.stop()
		if check =='b':
			BOOTSTRAPSITES_COUNTER -= 1
		else:
			PREFETCHING_COUNTER -= 1
		return


	del profile
	browser.quit()
	del browser
	
	if check =='b':
		BOOTSTRAPSITES_COUNTER -= 1
	else:
		PREFETCHING_COUNTER -= 1
	
	display.stop()



def bootstrap(a):

	global BOOTSTRAPSITES, BOOTSTRAPSITES_COUNTER
	print "Bootstraping Thread ...\n"

	while True:

		if len (BOOTSTRAPSITES ) > 0:

			for item in BOOTSTRAPSITES.keys():

				if BOOTSTRAPSITES_COUNTER < 5:
					if BOOTSTRAPSITES [item][1] <= time.time():						
						print ('BOOTSTRAP: ', item, 'FOR: ',BOOTSTRAPSITES[item][0] )
						log_string = 'BOOTSTRAP: '+str(time.time()) +' :'+item
						logger_1.info(log_string)
						BOOTSTRAPSITES_COUNTER +=1
	
						try:
							thread.start_new_thread( openPage, (item, 'b', ))
						except:
							pass

						BOOTSTRAPSITES [item][0]-=1
						BOOTSTRAPSITES [item][1]=time.time()+constants.INTERVAL_BOOTSTRAP
						print BOOTSTRAPSITES [item][1]
						
						if BOOTSTRAPSITES [item][0] <=0 :
							print 'ADDES TO PREFETCHING_LIST'
							log_string = 'BOOTSTRAP: ADDED_TO_PREFETCHING_LIST: '+item
							logger_1.info(log_string)
							PREFETCHING_LIST.append(item)
							del BOOTSTRAPSITES[item]

				while BOOTSTRAPSITES_COUNTER >=5:
					time.sleep(1)







def sitesPrefetching (number):
	PREFETCHING_BOOL = False
	
	while True:

		global PREFETCHING_QUEUE , TIME, PREFETCHING_LIST, PREFETCHING_COUNTER
		startTime = time.time()

		if len(PREFETCHING_LIST) > 0:
			PREFETCHING_QUEUE = calculateUtilities()

		while not PREFETCHING_QUEUE.empty():
			PREFETCHING_BOOL = True
			w = PREFETCHING_QUEUE.get()
			log_string = 'PREFETCHING: '+str(time.time()) +' :'+w[1]
			print log_string
			logger_1.info(log_string)
			try:
				PREFETCHING_COUNTER +=1
				thread.start_new_thread(openPage, (w[1] , 'p', ))
			except:
				pass

			while PREFETCHING_COUNTER >=5:
				time.sleep(1)

			if time.time() - startTime >= TIME:
				break # we have reached the end of the slot for prefetching we should stop and start the next slot

		if PREFETCHING_BOOL:
			if time.time() - startTime < TIME:
				print 'Going to sleep:' + str(TIME) +' '+str(time.time() - startTime)
				time.sleep(TIME - (time.time() - startTime))



def receiveLogs(num):

	global ALL_WEBSITES
	CONTROLLER_IP = constants.CONTROLLER_IP
	print CONTROLLER_IP
	CONTROLLER_PORT = constants.CONTROLLER_PORT_LOGS
	print CONTROLLER_PORT
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
				logger_1.info(log_string)

	return


	# tmp = [ ('http://www.cnn.com/', 10), ('http://www.bbc.com/', 10), ('http://www.yahoo.com/', 10), ('http://www.apple.com/', 10), ('http://www.souq.com/', 10),('http://www.faiza.com/', 10), ('http://www.ebay.com/', 10) ]
	
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
		print 'Calculating-Utilities ...'
		n_t = float(0.000)
		d_t = float(0.000)
		n_b = float(0.000)
		d_b = float(0.000)
		webPageObjects = ALL_WEBSITES[webpage].objects
		logger_2.info('Utility Calculation: ' + webpage)
		for o in webPageObjects.keys():
			x1, x2, x3, x4, st = webPageObjects[o].calculateUtilities()
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
		logger_1.info(log_string)
		logger_2.info(log_string)
		if t != 0:
			t = 1/t

		PREFETCHING_QUEUE.put((t, webpage))
	return PREFETCHING_QUEUE



