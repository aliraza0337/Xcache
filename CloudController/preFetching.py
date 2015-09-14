import time
import thread

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.proxy import *
import selenium.webdriver.firefox.webdriver as fwb
import socket as dummysocket
import cPickle
import Queue as Q 
import controller 
global ALL_WEBSITES, All_Webpages
All_Webpages = Q.PriorityQueue()

ALL_WEBSITES = {}
ALL_WEBSITES['http://www.yasirzaki.net/'] = ''
ALL_WEBSITES['http://www.ebay.com/']=''

All_Webpages.put(( time.time() + 0 ,'http://www.yasirzaki.net/'))
All_Webpages.put(( time.time() + 0 ,'http://www.ebay.com/'))

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
		#print 'Stuck here'
		browser.get (webpage)
		time.sleep(0.001)

	time.sleep(1)
	browser.set_window_size(1024, 768)
	browser.get (webpage)
	while browser.title == "Problem loading page":
		#print 'Stuck here 2 '
		browser.get (webpage)
		time.sleep(0.001)
	
	del profile
	print "-- Finished loading ", browser.title
	browser.quit()
	del browser





def sitesPrefetching (number):
	global ALL_WEBSITES, All_Webpages

	while True:
		global ALL_WEBSITES
		print 'Here'
		display = Display(visible=0, size=(1920,1080))
		display.start()

		
		currentTime = time.time()

		a = All_Webpages.get()
		print a[1]
		if a[0] < currentTime+10:
			webpage = a[1]

			print webpage
			openPage(webpage)
			
			newPriority = time.time()+controller.getThePriority(webpage)
			print newPriority
			All_Webpages.put((newPriority, webpage))
			display.stop()
		else:
			newPriority = time.time()+controller.getThePriority(webpage)
			All_Webpages.put((newPriority, webpage))
		#time.time(30)







def receiveLogs(num):
	global ALL_WEBSITES, All_Webpages

	CONTROLLER_IP = '10.225.3.124'
	CONTROLLER_PORT = 7007

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
		
		for web in websites:
			if not (web in ALL_WEBSITES): 
				ALL_WEBSITES[web] = ''
				All_Webpages.put(( time.time() + 1800 ,web))
