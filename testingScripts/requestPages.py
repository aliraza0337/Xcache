import time
import thread
import copy
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.proxy import *
import selenium.webdriver.firefox.webdriver as fwb
import socket as dummysocket
import cPickle
import logging
import random 

#logging.basicConfig(filename='userRequests.log',level=logging.INFO)
ALL_WEBSITES = []

def openPage (webpage):

	myProxy = "10.230.240.204:60001"
	proxy = Proxy ({
		'proxyType':ProxyType.MANUAL,
		'httpProxy': myProxy,
		'ftpProxy': '',
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
	# profile.add_extension( 'modify_headers-0.7.1.1-fx.xpi')
	# profile.set_preference('modifyheaders.headers.count', 1)
	# profile.set_preference('modifyheaders.headers.action0', "Add")
	# profile.set_preference('modifyheaders.headers.name0', 'webpage')
	# profile.set_preference('modifyheaders.headers.value0', webpage)
	# profile.set_preference('modifyheaders.headers.enabled0', True)
	# profile.set_preference('modifyheaders.config.active', True)
	# profile.set_preference('modifyheaders.config.alwaysOn', True)
	#

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
	#print "-- Finished loading ", browser.title
	browser.quit()
	del browser



def readtxtFile(filename):
	f = open(filename, 'r')
	while 1:

		line = f.readline()
		if not line:
			break 
		ALL_WEBSITES.append('http://www.'+line.split('\n')[0]+'/')
	return ALL_WEBSITES



def StartPrefectching():
	webpages = readtxtFile('websites.txt')
	total_webpages =  len(webpages)
	while 1:
		display = Display(visible=0, size=(1920,1080))
		display.start()
		w = random.randint(0, total_webpages-1)
		timeToSleep = random.randint(100, 150)
		print webpages[w]
		try:
			openPage(webpages[w])
		except:
			pass
		display.stop()
		#time.sleep(timeToSleep)
		log_string = 'REQUESTING: '+ str(time.time())+ ': '+webpages[w]
		print log_string
		#logging.info(log_string)


StartPrefectching()
