from __future__ import absolute_import, division, print_function, unicode_literals

import re
from functools import wraps
import string

__author__ = "Richard Eames <reames@asymmetricventures.com"
__date__ = "Jun 26, 2013"

def err(fn, name = None):
	fn_name = fn.__name__ if name is None else name
	
	@wraps(fn)
	def wrapper(*args, **kwargs):
		try:
			return fn(*args, **kwargs)
		except Exception as e:
			import traceback
			traceback.print_exc()
			raise Exception("Invalid {} TAG: {}".format(fn_name, e))
	return wrapper

class Parser(object):
	""" http://www.whatwg.org/specs/web-apps/current-work/multipage/syntax.html#syntax """
	
	def __init__(self, html):
		self.html = html
		self.ihtml = html.lower()
		self.offset = 0
		
		self._ws = list(string.whitespace)
		self._qq = ('"', "'")
		
		self.matched_data = ""
	
	@property
	def at_end(self):
		return self.offset >= len(self.html)
	
	def _src(self, ignore_case):
		return self.ihtml if ignore_case else self.html
	
	def c(self, ignore_case = True):
		return self._src(ignore_case)[self.offset]
	
	# Lexing functions
	def expect(self, s, ignore_case = True):
		src = self._src(ignore_case)
		
		def _i(ss):
			return ss.lower() if ignore_case else ss
		
		if isinstance(s, (list, tuple)):
			for item in s:
				if src[self.offset:].startswith(_i(item)):
					self.offset += len(item)
					self.matched_data += item
					return item
		
		elif src[self.offset:].startswith(_i(s)):
			self.offset += len(s)
			self.matched_data += s
			return s
		
		raise Exception("Expected '{}'".format(s))
	
	def _eat_matches(self, s, ignore_case):
		src = self._src(ignore_case)
		matches = 0
		round_match = False
		
		if isinstance(s, (list, tuple)):
			while not self.at_end:
				round_match = False
				for item in s:
					if src[self.offset:].startswith(item):
						round_match = True
						matches += 1
						self.offset += len(item)
						self.matched_data += item
				
				if not round_match:
					break;
		else:
			while not self.at_end:
				round_match = False
				if src[self.offset:].startswith(s):
					round_match = True
					matches += 1
					self.offset += len(s)
					self.matched_data += s
				
				if not round_match:
					break
		
		return matches
	
	def one_or_more(self, s, ignore_case = True):
		matches = self._eat_matches(s, ignore_case)
		
		if matches < 1:
			raise Exception("Expected one or more matches of '{}'".format(s))
	
	def zero_or_more(self, s, ignore_case = True):
		self._eat_matches(s, ignore_case)
	
	def eat_white(self):
		start = self.offset
		while not self.at_end and self.html[self.offset] in string.whitespace:
			self.matched_data += self.html[self.offset]
			self.offset += 1
		
		return self.html[start:self.offset]
	
	def is_next(self, t, ignore_case = True):
		src = self._src(ignore_case)
		
		if isinstance(t, (list, tuple)):
			return any((src[self.offset:].startswith(c) for c in t))
		
		return src[self.offset:].startswith(t)
	
	def match(self, rx, ignore_case = True):
		""" Like is_next() but uses regex """
		matcher = re.compile(rx, re.IGNORECASE if ignore_case else 0)
		
		return bool(matcher.match(self.html[self.offset:]))
	
	def consume(self, rx, ignore_case = True):
		""" Like expect() but uses regex """
		matcher = re.compile(rx, re.IGNORECASE if ignore_case else 0)
		match = matcher.match(self._src(ignore_case)[self.offset:])
		if not match:
			raise Exception("Expected string like {}".format(rx))
		
		self.offset += len(match.group(0))
		self.matched_data += match.group(0)
		return match.group(0)
	
	def data(self):
		d = self.matched_data
		self.matched_data = ""
		return d
	
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
	
	def comments_or_space(self):
		ret = []
		while not self.at_end:
			ret.append(self.eat_white())
			if self.is_next('<!--'):
				ret.append(self.COMMENT())
				ret.append(self.eat_white())
			else:
				break
		
		self.data()
		
		return filter(None, ret)
	
	# AST functions
	@err
	def DOCTYPE(self):
		self.expect('<!doctype')
		self.eat_white()
		self.expect('html')
		
		if self.is_next(self._ws):
			"Possibly the legacy or obsolete string next"
			self.one_or_more(self._ws)
			
			if self.is_next('"system"'):
				self.expect('"system"')
				self.one_or_more(self._ws)
				q = self.c()
				self.expect(self._qq)
				self.expect("about:legacty-compay", False)
				self.expect(q)
			
			elif self.is_next('"public"'):
				self.expect('"public"')
				self.one_or_more(self._ws)
				q = self.c()
				self.expect(self._qq)
				
				obsolete_doctypes = {
					"-//W3C//DTD HTML 4.0//EN" :"http://www.w3.org/TR/REC-html40/strict.dtd",
					"-//W3C//DTD HTML 4.01//EN" :"http://www.w3.org/TR/html4/strict.dtd",
					"-//W3C//DTD XHTML 1.0 Strict//EN" :"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd",
					"-//W3C//DTD XHTML 1.1//EN" :"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd",
				}
				empty_obsolete_doctypes = ("-//W3C//DTD HTML 4.0//EN", "-//W3C//DTD HTML 4.01//EN")
				is_empty_public_identifier = False
				if self.is_next(empty_obsolete_doctypes, ignore_case = False):
					# These two can have an empty system identifier
					is_empty_public_identifier = True
				
				public_identifier = self.expect(empty_obsolete_doctypes, ignore_case = False)
				self.expect(q)
				
				if self.match(r'\s*["\']'):
					# we're expecting a system identifier
					system_identifier = obsolete_doctypes[public_identifier]
					self.one_or_more(self._ws)
					q = self.c()
					self.expect(self._qq)
					self.expect(system_identifier, ignore_case = False)
					self.expect(q)
					
				elif not is_empty_public_identifier:
					raise Exception("Expected system identifier in doctype")
			
		self.zero_or_more(self._ws)
		self.expect('>')
		
		return ('DOCTYPE', self.data())
	
	@err
	def COMMENT(self):
		self.expect('<!--')
		if self.match(r'\-?>'):
			raise Exception("Comments cannot start with '-' or '->'")
		self.consume(r'.*?(?=\-\-)')
		if self.is_next('--'):
			self.expect('--')
			if not self.is_next('>'):
				raise Exception("Comments cannot contain '--'")
			self.expect('>')
		else:
			raise Exception("Invalid comment, could not find ending")
		
		return ('COMMENT', self.data())
	
	def _start_tag(self, name, can_close = False):
		self.expect('<')
		self.expect(name)
		attrs = []
		while self.is_next(self._ws):
			attrs.push(self._parse_attr())
		
		self.one_or_more(self._ws)
		if can_close and self.is_next('/'):
			self.expect('/')
		self.expect('>')
		
		return (name, self.data(), attrs)
	
	def _end_tag(self, name):
		self.expect('<')
		self.expect(name)
		self.zero_or_more(self._ws)
		self.expect('>')
		return (name, self.data())
	
	def void_tag(self, name):
		return self._start_tag(name, True)
	
	def raw_tag(self, name):
		pass
	
	def eraw_tag(self, name):
		pass
	
	def foreign_tag(self, name):
		start_tag = self._start_tag(name, True)
		if start_tag[1][-2] == '/':
			# this is a self closing tag
			return (name, start_tag, [], None)
	
	def normal_tag(self, name):
		pass
	

	
	def _parse_attr(self):
		self.expect(self._ws)
		self.data() # ignore ws
		
		attr_name = self.expect(string.ascii_letters)
		if self.match(r'\s*='):
			self.eat_white()
			self.expect('=')
			self.eat_white()
			
			if self.is_next(self._qq):
				attr_value = self._parse_string()
			else:
				attr_value = self.expect(string.ascii_letters + '_')
			
			return [attr_name, self.data(), attr_value]
			
		else:
			# empty attribute
			return [attr_name, self.data(), ""]
	
	def _parse_string(self):
		q = self.c()
		self.expect(self._qq)
		
		self.consume(r'(?:[^{}\\]|\\.)*'.format(q))
		self.expect(self._qq)
		return self.data()

_fn_map = {
	'void' : Parser.void_tag,
	'raw' : Parser.raw_tag,
	'eraw' : Parser.eraw_tag,
	'foreign' : Parser.foreign_tag,
	'normal' : Parser.normal_tag
}

t = (
	'HEAD', 'TITLE', 'BASE', 'LINK', 'META', 'STYLE', 'SCRIPT', 'NOSCRIPT',
	'BODY', 'ARTICLE', 'SECTION', 'NAV', 'ASIDE', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'HGROUP', 'HEADER', 'FOOTER', 'ADDRESS',
	'P', 'HR', 'PRE', 'BLOCKQUOTE', 'OL', 'UL', 'LI', 'DL', 'DT', 'FIGURE', 'FIGCAPTION', 'MAIN', 'DIV',
	'A', 'EM', 'STRONG', 'SMALL', 'S', 'CITE', 'Q', 'DFN', 'ABBR', 'DATA', 'TIME', 'CODE', 'VAR', 'SAMP', 'KBD', 'SUB', 'SUP', 'I', 'B', 'U', 'MARK', 'RUBY', 'RT', 'RP', 'BDI', 'BDO', 'SPAN', 'BR', 'WBR',
	'INS', 'DEL',
	'IMG', 'IFRAME', 'EMBED', 'OBJECT', 'PARAM', 'VIDEO', 'AUDIO', 'SOURCE', 'TRACK', 'CANVAS', 'MAP', 'AREA',
	'TABLE', 'CAPTION', 'COLGROUP', 'COL', 'TBODY', 'THEAD', 'TFOOT', 'TR', 'TH', 'TD',
	'FORM', 'FIELDSET', 'LEGEND', 'LABEL', 'INPUT', 'BUTTON', 'SELECT', 'DATALIST', 'OPTGROUP', 'OPTION', 'TEXTAREA', 'KEYGEN', 'OUPUT', 'PROGRESS', 'METER',
	'DETAILS', 'SUMMARY', 'MENU', 'MENUITEM',
)


def tag(name, tp = 'void'):
	fn = _fn_map.get(tp, Parser.normal_tag)
	
	return lambda self: fn(self, name)
setattr(Parser, 'HTML', err(tag('HTML'), 'HTML'))

for e in t:
	setattr(Parser, e, err(tag(e), e))
	
	
