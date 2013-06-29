from __future__ import unicode_literals, division, absolute_import, print_function

import html5lib
from .utils import indent_text

__author__ = "richard"
__created__ = "Jun 28, 2013"

class JSDomTemplate(object):
	
	tpl = """\
define([], function() {{
	var C = document.createElement;
	var T = document.createTextNode;
	
	function TPL({tpl_args}) {{
		var $root = document.createDocumentFragment();
		{node_creation}
		
		{tpl_body}
		
		return $root;
	}}
	return TPL;
}});"""
	
	def __init__(self, text):
		self.text = text
		self.doc = html5lib.parseFragment(text)
		self.node_counts = {}
		
		self.needed_args = set()
		self.tpl_vars = {}
		self.text_vars = {}
	
	def _get_var(self, name):
		self.node_counts.setdefault(name.lower(), -1)
		self.node_counts[name.lower()] += 1
		
		return "_{}{}".format(name.lower(), self.node_counts[name.lower()])
	
	def _get_text_var(self):
		self.node_counts.setdefault("$text", -1)
		self.node_counts["$text"] += 1
		
		return "$text{}".format(self.node_counts["$text"])
	
	def _walk_doc(self):
		self._walk_children(self.doc)
	
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
	
