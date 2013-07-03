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
	
	function TPL({tpl_args}) {{
		{tpl_body}
	}}
	return TPL;
}});"""
	
	def __init__(self, text):
		self.text = text
		self.doc = html5lib.parseFragment(text, treebuilder = "dom")
		self.node_counts = {}
		
		self.needed_args = OrderedDict()
		self.tpl_vars = []
		self.text_vars = {}
	
	def get_template(self):
		return self.tpl.format(
			requirements = ', '.join("'{}'".format(arg) for arg in self.needed_args.keys()),
			require_args = ', '.join(arg for arg in self.needed_args.values()),
			tpl_args = ', '.join(arg for arg in self.tpl_vars),
			
			tpl_body = ''
		)
	
	def _get_var(self, name):
		self.node_counts.setdefault(name.lower(), -1)
		self.node_counts[name.lower()] += 1
		
		return "_{}{}".format(name.lower(), self.node_counts[name.lower()])
	
	def _get_text_var(self):
		self.node_counts.setdefault("$text", -1)
		self.node_counts["$text"] += 1
		
		return "$text{}".format(self.node_counts["$text"])
	
	def _get_root(self):
		self.node_counts.setdefault('$root', -1)
		self.node_counts['$root'] += 1
		return "$root{}".format(self.node_counts['$root']);
	
	def _walk_doc(self):
		
		for child in self.doc.childNodes:
			if child.nodeType == child.COMMENT_NODE:
				comment_data = child.nodeValue.strip()
				
				if re.match(r'^\s*require\([^\)]*\)\s*$', comment_data):
					st = parser.expr(comment_data)
					c = st.compile()
					ret = eval(c, {'require' : lambda x:x})
					if not isinstance(ret, dict):
						raise Exception("Found a require() comment that does not specify a dict")
					self.needed_args = OrderedDict(ret)
				
				elif re.match(r'^\s*globals\([^\)]*\)\s*$', comment_data):
					st = parser.expr(comment_data)
					c = st.compile()
					ret = eval(c, {'globals' : lambda *args: list(args)})
					if not isinstance(ret, list):
						raise Exception("Found a globals() comment that does not specify a list of globals")
					self.tpl_vars = ret
					
			else:
				self._walk_node(child)
	
	def _walk_children(self, node):
		
		for child in node.childNodes:
			creation_text, setup_text = self._walk_node(child)
	
	def _walk_node(self, node):
		name = node.nodeName.lower()
		if name != '#text' and name.startswith('#'):
			# ignore
			return '', ''
		
		if name == '#text':
			var_name = self._get_text_var()
			node_value = self._parse_text_node_value(node.data)
	
	def _parse_text_node_value(self, value):
		
		return value.replace('\n', '\\n').encode('ascii', 'xmlcharrefreplace')
	
