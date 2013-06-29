from __future__ import absolute_import, division, print_function, unicode_literals

import html5lib
import urllib
from jsdompl.utils import indent_text

__author__ = "Richard Eames <reames@asymmetricventures.com>"
__date__ = "Jun 26, 2013"


doc = html5lib.parseFragment("""
<a href="{{ url('foo') }}" >{{ tag }}</a>
""", treebuilder = "dom")

node_counts = {}

def parse_attr_value(value):
	
	tvalue = value.strip()
	if tvalue.startswith('{{') and tvalue.endswith('}}'):
		return tvalue[2:-2]
	
	return '''"{}"'''.format(value)

def append_children(root_name, child_names):
	return '\n'.join(("{}.appendChild({});".format(root_name, node_name) for node_name in child_names));

def walk_node(node):
	creation_text = ""
	setup_text = ""
	name = node.nodeName.lower()
	if name != "#text" and name.startswith('#'):
		return '', '', ''
	
	node_counts.setdefault(name, -1)
	node_counts[name] += 1
	
	if name == "#text":
		var_name = "$text_node{}".format(node_counts[name])
		var_text = node.data.replace('\n', '\\n').encode('ascii', 'xmlcharrefreplace')
		creation_text = '''var {} = T("{}");\n'''.format(var_name, var_text)
		return var_name, creation_text, setup_text 
	
	var_name = "_{}{}".format(name, node_counts[name])
	
	creation_text = "var {} = C('{}');\n".format(var_name, name)
	
	if node.hasAttributes():
		for k, v in node.attributes.items():
			setup_text += '''{}.setAttribute("{}", {});\n'''.format(var_name, k, parse_attr_value(v))
	
	nodes_names, new_nodes, nodes_setup = walk_children(node)
	
	setup_text += '\n'.join(new_nodes) + '\n'.join(nodes_setup)
	setup_text += append_children(var_name, nodes_names)
	
	return var_name, creation_text, setup_text

def walk_children(node):
	node_names = []
	new_nodes = []
	nodes_setup = []
	
	for child in  node.childNodes:
		var_name, creation_text, setup_text = walk_node(child)
		node_names.append(var_name)
		new_nodes.append(creation_text)
		nodes_setup.append(setup_text)
	return node_names, new_nodes, nodes_setup

def walk_doc(doc):
	node_names, new_nodes, nodes_setup = walk_children(doc)
	
	setup_text = '\n'.join(new_nodes) + '\n'.join(nodes_setup)
	
	return setup_text + append_children("$root", node_names)
		

tpl = """
define([], function() {{
	var C = document.createElement;
	var T = document.createTextNode;
	function TPL() {{
		var $root = document.createDocumentFragment();
{tpl_body}
		return $root;
	}}
	return TPL;
}});""".format(tpl_body = indent_text(walk_doc(doc), 2))

print(tpl)
