class HTTPObject:
	def __init__(self, headers, url, content, status, reason, request_ver ):
		
		self.request_ver = request_ver
		self.headers = headers
		self.url = url
		self.content = content
		self.hash = 0
		self.status = status
		self.reason = reason
		self.diff = False 
		self.canApplyDiff = False
		self.belongsTo = belongsTo