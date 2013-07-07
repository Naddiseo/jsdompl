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
		'HTML_DOCTYPE', 'HTML_STARTTAG', 'HTML_ENDTAG', 'HTML_EMPTYTAG',
		'JS_OPEN', 'ESCAPED_OPEN', 'EXPRESSION_OPEN'
	])
	
	ttype = {
		'{%'  : 'JS_TERMINATOR',
		'{{'  : 'ESCAPED_TERMINATOR',
		'{{{' : 'EXPRESSION_TERMINATOR'
	}
	
	tbtype = {
		'{%'  : 'JS_OPEN',
		'{{'  : 'ESCAPED_OPEN',
		'{{{' : 'EXPRESSION_OPEN'
	}
	
	def input(self, text):
		self.lexer = HTMLTokenizer(text)
		self.lexpos = 0
		self.lineno = 0
	
	def build(self, **kwargs):
		pass
	
	def _html_token(self):
		for t in self.lexer:
			yield t
	
	def token(self):
		if self.next_tokens:
			return self.next_tokens.pop(0)
		
		try:
			html_tok = next(self._html_token())
			self.lexpos += len(html_tok['data'])
			self.lineno = self.lexer.stream.position()[0]
		except StopIteration:
			return None
		
		tok = self._lextoken_from_html(html_tok)
		
		if tok.type == 'HTML_CHARS':
			# possibly js
			endtext = self._parse_chars(tok.value['data'])
			
			while endtext is not None:
				endtext = self._parse_chars(endtext)
			
			return self.next_tokens.pop(0)
			
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
		token.lineno = self.lineno
		token.lexpos = self.lexpos
		
		token.value = {
			'self_closing' : html_token.get('selfClosing', False),
			'name' : html_token.get('name', None),
		}
		
		if isinstance(html_token['data'], (list, tuple)):
			token.value['attrs'] = html_token['data']
			token.value['data'] = ''
		else:
			token.value['data'] = html_token['data']
		
		if token.type == tokenTypes['ParseError']:
			raise SyntaxError("Got HTML Parse Error for token {}".format(html_token))
		
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
			return None
		
		pretext = m.group(1)
		start_type = m.group(2)
		
		self.lexpos -= len(data)
		
		if len(pretext):
			pretext_tok = LexToken()
			pretext_tok.type = 'HTML_CHARS'
			pretext_tok.value = pretext
			pretext_tok.lineno = self.lineno - pretext.count("\n")
			pretext_tok.lexpos = self.lexpos
			self.next_tokens.append(pretext_tok)
			self.lexpos += len(pretext)
		
		start_tok = LexToken()
		start_tok.type = self.tbtype[start_type]
		start_tok.value = start_type
		start_tok.lineno = self.lineno
		start_tok.lexpos = self.lexpos
		self.next_tokens.append(start_tok)
		self.lexpos += len(start_type)
		
		js_lexer = JSLexer()
		js_lexer.input(data[m.end(2):])
		for t in js_lexer:
			t.lineno += self.lineno - 1
			t.lexpos = self.lexpos
			self.lexpos += js_lexer.lexer.lexpos
			
			if t.type in ('EXPRESSION_TERMINATOR', 'ESCAPED_TERMINATOR', 'JS_TERMINATOR'):
				if t.type != self.ttype[start_type]:
					raise SyntaxError("Expected {} but got {} in char data `{}`".format(self.ttype[start_type], t.type, data))
				self.next_tokens.append(t)
				break
			
			self.next_tokens.append(t)
		remaining_text = data[m.end(2) + js_lexer.lexer.lexpos:]
		self.lexpos += len(remaining_text)
		return remaining_text
