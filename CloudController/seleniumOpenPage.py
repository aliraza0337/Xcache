import time
import thread
import copy
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.proxy import *
import selenium.webdriver.firefox.webdriver as fwb
import socket as dummysocket

def openPage (webpage, port):

	display = Display(visible=0, size=(1920,1080))

	myProxy = "127.0.0.1:"+str(port)
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

