from __future__ import absolute_import, division, print_function, unicode_literals

__author__ = "Richard Eames <reames@asymmetricventures.com>"
__date__ = "Jul 4, 2013"

import re

from html5lib.constants import tokenTypes
from html5lib.tokenizer import HTMLTokenizer
from ply.lex import LexToken

from .jslexer import Lexer as JSLexer

js_start_rx = re.compile(r'^(.*?)(\{(?:%|\{(?:\{)?))', re.DOTALL)

def lex_token__str__(self):
	name = ''
	self_closing = ''
	if hasattr(self, 'name'):
		name = self.name
	
	if hasattr(self, 'self_closing'):
		self_closing = self.self_closing
	
	return 'LexToken(%s, %r, %d, %d, <%s>, %s)' % (self.type, self.value, self.lineno, self.lexpos, name, self_closing)

setattr(LexToken, '__str__', lex_token__str__)

class Lexer(JSLexer):
	tokens = tuple(list(JSLexer.tokens) + [
		'HTML_CHARS', 'HTML_WS', 'HTML_COMMENT',
		'HTML_DOCTYPE', 'HTML_STARTTAG', 'HTML_ENDTAG', 'HTML_EMPTYTAG'
	])
	
	def input(self, text):
		self.lexer = HTMLTokenizer(text)
	
	def build(self, **kwargs):
		pass
	
	def _html_token(self):
		for t in self.lexer:
			yield t
	
	def token(self):
		if self.next_tokens:
			return self.next_tokens.pop(0)
		
		html_tok = next(self._html_token())
		
		tok = self._lextoken_from_html(html_tok)
		
		if tok.type == 'HTML_CHARS':
			# possibly js
			pretext, endtext = self._parse_chars(tok.value)
			if pretext is not None:
				tok.value = pretext
			
			while endtext is not None:
				pretext, endtext = self._parse_chars(endtext)
				if pretext is not None:
					endtok = LexToken()
					endtok.type = tok.type
					endtok.lineno = tok.lineno
					endtok.lexpos = tok.lexpos
					endtok.value = pretext
					self.next_tokens.append(endtok)
			
		return tok
	
	def _lextoken_from_html(self, html_token):
		token = LexToken()
		token.type = {
			0 : 'HTML_DOCTYPE',
			1 : 'HTML_CHARS',
			2 : 'HTML_WS',
			3 : 'HTML_STARTTAG',
			4 : 'HTML_ENDTAG',
			5 : 'HTML_EMPTYTAG',
			6 : 'HTML_COMMENT',
			7 : 'HTML_PARSEERROR',
		}[html_token['type']]
		# TODO: fix lineno/lexpos
		token.lineno = 0
		token.lexpos = 0
		
		token.value = html_token['data']
		
		if token.type == tokenTypes['ParseError']:
			raise SyntaxError("Got HTML Parse Error for token {}".format(html_token))
		
		if 'selfClosing' in html_token:
			token.self_closing = html_token['selfClosing']
		
		if 'name' in html_token:
			token.name = html_token['name']
		
		return token
	
	def __iter__(self):
		return self
	
	def next(self):
		token = self.token()
		if not token:
			raise StopIteration()
		return token
	
	def _parse_chars(self, data):
		m = js_start_rx.match(data)
		
		if m is None:
			return None, None
		
		pretext = m.group(1)
		start_type = m.group(2)
		ttype = {
			'{%'  : 'JS_TERMINATOR',
			'{{'  : 'ESCAPED_TERMINATOR',
			'{{{' : 'EXPRESSION_TERMINATOR'
		}
		
		js_lexer = JSLexer()
		js_lexer.input(data[m.end(2):])
		for t in js_lexer:
			if t.type in ('EXPRESSION_TERMINATOR', 'ESCAPED_TERMINATOR', 'JS_TERMINATOR'):
				if t.type != ttype[start_type]:
					raise SyntaxError("Expected {} but got {} in char data `{}`".format(ttype[start_type], t.type, data))
				break
			
			self.next_tokens.append(t)
			
		endtext = data[m.end(2) + js_lexer.lexer.lexpos:]
		return pretext, endtext
