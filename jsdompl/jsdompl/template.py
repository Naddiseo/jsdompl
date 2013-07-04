from __future__ import unicode_literals, division, absolute_import, print_function

import re
import parser
from collections import OrderedDict

import html5lib

from .utils import indent_text

__author__ = "richard"
__created__ = "Jun 28, 2013"

class JSDomTemplate(object):
	
	tpl = """\
define([{requirements}], function({require_args}) {{
	var C = document.createElement;
	var T = document.createTextNode;
	var F = document.createDocumentFragment;
	
	function $Template({tpl_args}) {{
{tpl_body}
	}}
	return $Template;
}});"""
	
	def __init__(self, text):
		self.text = text
		self.doc = html5lib.parseFragment(text, treebuilder = "dom")
		self.node_counts = {}
		
		self.needed_args = OrderedDict()
		self.tpl_vars = []
		self.text_vars = {}
		
		self.state_stack = []
		self.output = ''
		self.root_stack = []
		self.var_name = ''
	
	def get_template(self):
		self._walk_doc()
		return self.tpl.format(
			requirements = ', '.join("'{}'".format(arg) for arg in self.needed_args.keys()),
			require_args = ', '.join(arg for arg in self.needed_args.values()),
			tpl_args = ', '.join(arg for arg in self.tpl_vars),
			
			tpl_body = indent_text(self.output, 2)
		)
	
	def _get_var(self, name):
		self.node_counts.setdefault(name.lower(), -1)
		self.node_counts[name.lower()] += 1
		
		return "_{}{}".format(name.lower(), self.node_counts[name.lower()])
	
	def _get_text_var(self):
		return self._get_var('$text')
	
	def _get_root(self):
		return self._get_var('$root')
	
	@property
	def root(self):
		return self.root_stack[-1]
	
	def _push_root(self, r):
		self.root_stack.append(r)
	
	def _pop_root(self):
		self.root_stack.pop()
	
	def _append(self, name):
		self.output += '{}.appendChild({});\n'.format(self.root, name)
	
	@property
	def state(self):
		return self.state_stack[-1]
	
	def _switch(self, state):
		if len(self.state_stack) and self.state == 'html':
			self.output += '");\n'
			#self.output += "\n"
			self.state_stack.pop()
		
		self.state_stack.append(state)
		if state == 'html':
			self.output += 'var {} = T("'.format(self._get_text_var())
		
		elif state == 'js expression':
			self.output += ');\n'
		
		elif state == 'js escaped expression':
			self.output += ');\n'
	
	def _walk_doc(self):
		doc = self._get_root()
		self.output += 'var {} = F();\n'.format(doc)
		self._push_root(doc)
		self._switch('html')
		
		for child in self.doc.childNodes:
			if child.nodeType == child.COMMENT_NODE:
				comment_data = child.nodeValue.strip()
				
				if re.match(r'^\s*define\([^\)]*\)\s*$', comment_data):
					st = parser.expr(comment_data)
					c = st.compile()
					ret = eval(c, {'define' : lambda x:x})
					if not isinstance(ret, dict):
						raise Exception("Found a require() comment that does not specify a dict")
					self.needed_args = OrderedDict(ret)
				
				elif re.match(r'^\s*Template\([^\)]*\)\s*$', comment_data):
					st = parser.expr(comment_data)
					c = st.compile()
					ret = eval(c, {'Template' : lambda *args: list(args)})
					if not isinstance(ret, list):
						raise Exception("Found a Template() comment that does not specify a list of globals")
					self.tpl_vars = ret
					
			else:
				self._walk_node(child)
		
		self.output += 'return {};\n'.format(doc)
	
	def _walk_children(self, node):
		
		for child in node.childNodes:
			node_name = self._walk_node(child)
			if node_name:
				self._append(node_name)
	
	def _walk_node(self, node):
		name = node.nodeName.lower()
		node_var = self._get_var(name)
		if name != '#text' and name.startswith('#'):
			# ignore
			return '', ''
		
		if name == '#text':
			self._switch('html')
			self._parse_text_node_value(node.data)
			return ''
		else:
			s = self.state
			self._switch('js')
			self.output += 'var ${} = C("{}");\n'.format(node_var, name)
			self._switch(s)
		self._push_root(node_var)
		self._walk_children(node)
		self._pop_root()
		
		self._append(node_var)
		
		return node_var
	
	def _parse_text_node_value(self, value):
		""" Returns the javascript conversion of the textnode
		"""
		i = 0
		
		# State 1 - html
		# State 2 - html string
		# State 3 - js
		# State 4 - js expression
		# State 5 - js string
		
		
		while i < len(value):
			c = value[i]
			
			if self.state == 'html':
				if c == '{':
					c2 = value[i + 1]
					if c2 == '{': # possibly an expression escape
						c3 = value[i + 2]
						if c3 == '{':
							# Non escape expression
							self._switch('js expression')
							
							self.output += ');\n';
							self._append(self.var_name)
							self.var_name = self._get_var('$tmp')
							self.output += 'var {} = ('.format(self.var_name)
							
							i += 3
							continue
						else:
							# expression escape
							self._switch('js escape expression')
							self.output += ');\n'
							self._append(self.var_name)
							self.var_name = self._get_var('$tmp')
							self.output += 'var {} = _.escape('.format(self.var_name)
							i += 2
							continue
					
					elif c2 == '%': # js code
						self.output += '");\n'
						self._append(self.var_name)
						
						self._switch('js')
						i += 2
						continue
				elif c == '"':
					self.output += '\\"'
				
				elif c == '\n':
					self.output += '\\n'
				
				else:
					self.output += c
			
			elif self.state == 'js':
				if c == '%':
					c2 = value[i + 1]
					if c == '}':
						self.output += '");\nvar {} = T("'.format(self._get_text_var())
						i += 2
						self._switch('html')
					else:
						self.output += c
				else:
					self.output += c
			
			elif self.state == 'js expression':
				
				if c == '}':
					c2 = value[i + 1]
					if c == '}':
						c3 = value[i + 2]
						if c3 == '}':
							i += 3
							self._append(self.var_name)
							self._switch('html')
						else:
							raise Exception("Unexpected '}}' in unescaped expression")
					else:
						raise Exception("Unexpected '}' in unescaped expression `{}`".format(value))
				else:
					self.output += c
			
			elif self.state == 'js escape expression':
				
				if c == '}':
					c2 = value[i + 1]
					if c == '}':
						self.output += ');\nvar {} = T("'.format(self._get_text_var())
						i += 2
						self._switch('html')
					else:
						raise Exception("Unexpected '}' in escaped expression in `{}`".format(value))
				else:
					self.output += c
			
			i += 1
		
