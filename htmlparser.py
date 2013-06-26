from __future__ import absolute_import, division, print_function, unicode_literals

__author__ = "Richard Eames <reames@asymmetricventures.com"
__date__ = "Jun 26, 2013"

class Parser(object):
	""" http://www.whatwg.org/specs/web-apps/current-work/multipage/syntax.html#syntax """
	
	def __init__(self, html):
		self.html = html
		self.ihtml = html.lower()
		self.offset = 0
	
	# Lexing functions
	def iexpect(self, s):
		if self.ihtml[self.offset:].startswith(s):
			self.offset += len(s)
		else:
			raise Exception("Expected {}".format(s))
	def expect(self, s):
		if self.html[self.offset:].startswith(s):
			self.offset += len(s)
		else:
			raise Exception("Expected {}".format(s))
	
	def eat_white(self):
		pass
	
	def root(self):
		e = []
		
		for _ in self.comments_or_space():
			pass
		e.append(self.DOCTYPE())
		for _ in self.comments_or_space():
			pass
		e.append(self.HTML())
		for _ in self.comments_or_space():
			pass
		
		return e
	
	# AST functions
	def DOCTYPE(self):
		self.iexpect('<!doctype')
		
