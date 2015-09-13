# def setMaxAge(self, maxAge):
	# 	newH = []
	# 	for h in self.headers:
	# 		new_h = h
	# 		if h[0] == 'cache-control':
	# 			tok = h[1].split(',')
	# 			newstring = ""

 # 				for t in tok:
	# 				stringToAttach = t
	# 				if 'max-age' in t:
	# 					stringToAttach = "max-age="+str(maxAge)
 # 					if newstring == "":
	# 					newstring = stringToAttach
	# 				else:
	# 					newstring = newstring +","+stringToAttach

 # 				new_h = (h[0], newstring)

	# 	newH.append(new_h)
	# 	self.headers = newH