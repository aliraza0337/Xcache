class EdgeObject:
	def __init__(self, headers, url, content, status, reason, request_ver, diff, webpage, canApplyDiff):
		self.headers = headers
		self.url = url 
		self.content = content
		self.status = status
		self.reason = reason
		self.request_ver = request_ver
		self.diff = diff
		self.webpage = webpage
		self.canApplyDiff = canApplyDiff
