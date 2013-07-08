from __future__ import absolute_import, division, print_function, unicode_literals

__author__ = "Richard Eames <reames@asymmetricventures.com>"
__date__ = "Jul 5, 2013"

import re
import parser
from collections import OrderedDict

from .. import ast

class Visitor(object):
	def visit(self, node):
		method = 'visit_%s' % node.__class__.__name__
		return getattr(self, method, self.generic_visit)(node)

	def generic_visit(self, node):
#		if node is None:
#			return ''
#		return 'GEN: {}'.format(node)
		if node is None:
			return ''
		if isinstance(node, list):
			return '\n'.join(
				self.visit(child) for child in node
			)
		else:
			return '\n'.join (
				self.visit(child) for child in node.children()
			)
				

class JSDomplVisitor(Visitor):
	def __init__(self, js_parser = None):
		self.indent_level = 0
		self.root_count = -1
		self.text_count = -1
		self.roots = []
		self.html_count = -1
		
		self.children_to_add = [[]]
		
		self.needed_args = OrderedDict()
		self.tpl_args = []
		
		self.root_map = {}
		
		if js_parser is None:
			from jsdompl.parser import Parser
			js_parser = Parser(lex_optimize = False, lextab = '', yacc_optimize = False, yacctab = '', yacc_debug = False)
		
		self.p = js_parser
	
	def current_root(self):
		return self.roots[-1]
	
	def make_html_node(self, n):
		self.html_count += 1
		return "$${}{}".format(n, self.html_count)
	
	def make_root(self):
		self.root_count += 1
		return '$$root{}'.format(self.root_count)
	
	def make_text(self):
		self.text_count += 1
		return '$$text{}'.format(self.text_count)
	
	def add_child(self, child):
		self.children_to_add[-1].append(child)
	
	def push_scope(self, root = None):
		ret = ''
		if root is None:
			root = self.make_root()
			ret = '{}var {} = F();\n'
		self.root_map.setdefault(root, {})
		self.roots.append(root)
		self.children_to_add.append([])
		
		return ret.format(self.indent(), self.current_root())
	
	def pop_scope(self):
		ret = ''
		old_root = self.roots.pop()
		children_to_add = self.children_to_add.pop()
		
		for child in children_to_add:
			if child not in self.root_map[old_root]:
				ret += '{}{}.appendChild({});\n'.format(self.indent(), old_root, child)
				self.root_map[old_root][child] = 1
		
		if len(self.roots):
			if old_root not in self.root_map[self.current_root()]:
				ret += '{}{}.appendChild({});\n'.format(self.indent(), self.current_root(), old_root)
				self.root_map[self.current_root()][old_root] = 1
		return ret
	
	def indent(self):
		return '\t' * self.indent_level
	
	def visit_Program(self, node):
		ret = self.push_scope()
		ret += '\n'.join(self.visit(child) for child in node)
		ret += self.pop_scope()
		return ret
	
	def visit_Block(self, node):
		ret = '{\n'
		self.indent_level += 1
		ret += self.push_scope()
		
		ret += '\n'.join(
			"{}{}".format(self.indent(), self.visit(child)) for child in node
		)
		
		ret += self.pop_scope()
		self.indent_level -= 1
		ret += '\n' + self.indent() + '}\n'
		return ret
	
	def visit_HTMLJSContainer(self, node):
		return '\n'.join(
			'{}{}'.format(self.indent(), self.visit(child)) for child in node
		)
	
	def visit_VarStatement(self, node):
		return 'var {};'.format(', '.join(self.visit(child) for child in node))
	
	def visit_VarDecl(self, node):
		init = ''
		if node.initializer is not None:
			init = ' = {}'.format(self.visit(node.initializer))
		
		return 'var {}{}'.format(self.visit(node.identifier), init)
	
	def visit_Identifier(self, node):
		if hasattr(node, 'safe'):
			return node.value
		return "$_{}".format(node.value)
	
	def visit_Assign(self, node):
		if node.op == ':':
			template = '{}{} {}'
		else:
			template = '{} {} {}'
		if getattr(node, '_parens', False):
			template = '({})'.format(template)
		
		return template.format(self.visit(node.left), node.op, self.visit(node.right))
	
	def visit_GetPropAssign(self, node):
		template = 'get {}() {{\n{}\n{}}}'
		if getattr(node, '_parens', False):
			template = '({})'.format(template)
		body = ''
		self.indent_level += 1
		body += self.push_scope()
		body += '\n'.join(
			(self.indent() + self.visit(el)) for el in node.elements
		)
		body += self.pop_scope()
		self.indent_level -= 1
		return template.format(self.visit(node.prop_name), body, self.indent())

	def visit_SetPropAssign(self, node):
		template = 'set {}({}) {{\n{}\n{}}}'
		if getattr(node, '_parens', False):
			template = '({})'.format(template)
		if len(node.parameters) > 1:
			raise SyntaxError('Setter functions must have one argument: %s' % node)
		params = ','.join(self.visit(param) for param in node.parameters)
		body = ''
		self.indent_level += 1
		body += self.push_scope()
		body += '\n'.join(
			(self.indent() + self.visit(el)) for el in node.elements
		)
		body += self.pop_scope()
		self.indent_level -= 1
		return template % (self.visit(node.prop_name), params, body, self.indent())

	def visit_Number(self, node):
		return node.value

	def visit_Comma(self, node):
		s = '{}, {}'.format(self.visit(node.left), self.visit(node.right))
		if getattr(node, '_parens', False):
			s = '(' + s + ')'
		return s

	def visit_EmptyStatement(self, node):
		return node.value

	def visit_If(self, node):
		s = 'if ('
		if node.predicate is not None:
			s += self.visit(node.predicate)
		s += ') '
		s += self.visit(node.consequent)
		if node.alternative is not None:
			s += ' else '
			s += self.visit(node.alternative)
		return s

	def visit_Boolean(self, node):
		return node.value

	def visit_For(self, node):
		s = 'for ('
		if node.init is not None:
			s += self.visit(node.init)
		if node.init is None:
			s += ' ; '
		elif isinstance(node.init, (ast.Assign, ast.Comma, ast.FunctionCall,
									ast.UnaryOp, ast.Identifier, ast.BinOp,
									ast.Conditional, ast.Regex, ast.NewExpr)):
			s += '; '
		else:
			s += ' '
		if node.cond is not None:
			s += self.visit(node.cond)
		s += '; '
		if node.count is not None:
			s += self.visit(node.count)
		s += ') ' + self.visit(node.statement)
		return s

	def visit_ForIn(self, node):
		if isinstance(node.item, ast.VarDecl):
			template = 'for (var {} in {}) '
		else:
			template = 'for ({} in {}) '
		s = template.format(self.visit(node.item), self.visit(node.iterable))
		s += self.visit(node.statement)
		return s

	def visit_BinOp(self, node):
		if getattr(node, '_parens', False):
			template = '({} {} {})'
		else:
			template = '{} {} {}'
		return template.format(
			self.visit(node.left), node.op, self.visit(node.right))

	def visit_UnaryOp(self, node):
		s = self.visit(node.value)
		if node.postfix:
			s += node.op
		elif node.op in ('delete', 'void', 'typeof'):
			s = '{} {}'.format(node.op, s)
		else:
			s = '{}{}'.format(node.op, s)
		if getattr(node, '_parens', False):
			s = '({})'.format(s)
		return s

	def visit_ExprStatement(self, node):
		return '{};'.format(self.visit(node.expr))

	def visit_DoWhile(self, node):
		s = 'do '
		s += self.visit(node.statement)
		s += ' while ({});\n'.format(self.visit(node.predicate))
		return s

	def visit_While(self, node):
		s = 'while ({}) '.format(self.visit(node.predicate))
		s += self.visit(node.statement)
		return s

	def visit_Null(self, node):
		return 'null'

	def visit_String(self, node):
		return node.value

	def visit_Continue(self, node):
		if node.identifier is not None:
			s = 'continue {};\n'.format(self.visit_Identifier(node.identifier))
		else:
			s = 'continue;\n'
		return s

	def visit_Break(self, node):
		if node.identifier is not None:
			s = 'break {};\n'.format(self.visit_Identifier(node.identifier))
		else:
			s = 'break;\n'
		return s

	def visit_Return(self, node):
		if node.expr is None:
			return 'return;'
		else:
			return 'return {};'.format(self.visit(node.expr))

	def visit_With(self, node):
		s = 'with ({}) '.format(self.visit(node.expr))
		s += self.visit(node.statement)
		return s

	def visit_Label(self, node):
		s = '{}: {}'.format(self.visit(node.identifier), self.visit(node.statement))
		return s

	def visit_Switch(self, node):
		s = 'switch ({}) {{\n'.format(self.visit(node.expr))
		self.indent_level += 1
		for case in node.cases:
			s += self.indent() + self.visit_Case(case)
		if node.default is not None:
			s += self.visit_Default(node.default)
		self.indent_level -= 1
		s += self.indent() + '}'
		return s

	def visit_Case(self, node):
		s = 'case {}:\n'.format(self.visit(node.expr))
		self.indent_level += 1
		elements = '\n'.join(self.indent() + self.visit(element)
							 for element in node.elements)
		if elements:
			s += elements + '\n'
		self.indent_level -= 1
		return s

	def visit_Default(self, node):
		s = self.indent() + 'default:\n'
		self.indent_level += 1
		s += '\n'.join(self.indent() + self.visit(element)
					   for element in node.elements)
		if node.elements is not None:
			s += '\n'
		self.indent_level -= 1
		return s

	def visit_Throw(self, node):
		s = 'throw {};'.format(self.visit(node.expr))
		return s

	def visit_Debugger(self, node):
		return '{};'.format(node.value)

	def visit_Try(self, node):
		s = 'try '
		s += self.visit(node.statements)
		if node.catch is not None:
			s += ' ' + self.visit(node.catch)
		if node.fin is not None:
			s += ' ' + self.visit(node.fin)
		return s

	def visit_Catch(self, node):
		s = 'catch ({}) {}'.format(self.visit(node.identifier), self.visit(node.elements))
		return s

	def visit_Finally(self, node):
		s = 'finally {}'.format(self.visit(node.elements))
		return s

	def visit_FuncDecl(self, node):
		params = ', '.join(self.visit(param) for param in node.parameters)
		body = ''
		
		self.indent_level += 1
		body += '\n'.join(self.indent() + self.visit(element) for element in node.elements)
		self.indent_level -= 1

		return 'function {}({}) {{\n{}\n{}}}'.format(self.visit(node.identifier), params, body, self.indent())

	def visit_FuncExpr(self, node):
		self.indent_level += 1
		elements = '\n'.join(self.indent() + self.visit(element)
							 for element in node.elements)
		self.indent_level -= 1

		ident = node.identifier
		ident = '' if ident is None else ' %s' % self.visit(ident)

		header = 'function%s(%s)'
		if getattr(node, '_parens', False):
			header = '(' + header
		s = (header + ' {\n%s') % (
			ident,
			', '.join(self.visit(param) for param in node.parameters),
			elements,
			)
		s += '\n' + self.indent() + '}'
		if getattr(node, '_parens', False):
			s += ')'
		return s

	def visit_Conditional(self, node):
		if getattr(node, '_parens', False):
			template = '({} ? {} : {})'
		else:
			template = '{} ? {} : {}'

		s = template.format(
			self.visit(node.predicate),
			self.visit(node.consequent), self.visit(node.alternative)
		)
		return s

	def visit_Regex(self, node):
		if getattr(node, '_parens', False):
			return '({})'.format(node.value)
		else:
			return node.value

	def visit_NewExpr(self, node):
		s = 'new {}({})'.format(
			self.visit(node.identifier),
			', '.join(self.visit(arg) for arg in node.args)
			)
		return s

	def visit_DotAccessor(self, node):
		if getattr(node, '_parens', False):
			template = '({}.{})'
		else:
			template = '{}.{}'
		s = template.format(self.visit(node.node), self.visit(node.identifier))
		return s

	def visit_BracketAccessor(self, node):
		s = '{}[{}]'.format(self.visit(node.node), self.visit(node.expr))
		return s

	def visit_FunctionCall(self, node):
		s = '{}({})'.format(self.visit(node.identifier),
						', '.join(self.visit(arg) for arg in node.args))
		if getattr(node, '_parens', False):
			s = '(' + s + ')'
		return s

	def visit_Object(self, node):
		s = '{\n'
		self.indent_level += 1
		s += ',\n'.join(self.indent() + self.visit(prop)
						for prop in node.properties)
		self.indent_level -= 1
		if node.properties:
			s += '\n'
		s += self.indent() + '}'
		return s

	def visit_Array(self, node):
		s = '['
		length = len(node.items) - 1
		for index, item in enumerate(node.items):
			if isinstance(item, ast.Elision):
				s += ','
			elif index != length:
				s += self.visit(item) + ','
			else:
				s += self.visit(item)
		s += ']'
		return s

	def visit_This(self, node):
		return 'this'
	
	def visit_HTMLDataList(self, node):
		if len(node):
			node_parts = filter(lambda x: x and len(x), (self.visit(child) for child in node))
			txt_var = self.make_text()
			self.add_child(txt_var)
			ret = 'var {} = '.format(txt_var)
			
			ret += ' + '.join(node_parts)
			
			ret += ';\n'
			return ret
		return ''
	
	def visit_HTMLTag(self, node):
		var_name = self.make_html_node(node.name)
		ret = 'var {} = C("{}");\n'.format(var_name, node.name)
		self.add_child(var_name)
		if not node.void:
			ret += self.push_scope(var_name)
			
			ret += self.visit(node.inner)
			ret += self.pop_scope()
		if len(node.attrs):
			p = self.p
			
			for attr_name, attr_value in node.attrs:
				attr_ast = p.parse(attr_value)
				if isinstance(attr_ast, ast.Program):
					v = ''
					ret += self.push_scope()
					tmp_var = self.roots[-1]
					ret += self.visit(attr_ast.children())
					self.roots.pop()
					children_to_add = self.children_to_add.pop()
					
					for child in children_to_add:
						if child not in self.root_map[tmp_var]:
							ret += '{}{}.appendChild({});\n'.format(self.indent(), tmp_var, child)
							self.root_map[tmp_var][child] = 1
					v = tmp_var
				else:
					v = ''
				ret += '{}.setAttribute("{}", {});\n'.format(var_name, attr_name, v.replace('\n', '\\n').replace('"', '\\"'))
				
		
		return ret
	
	def visit_HTMLComment(self, node):
		comment_data = node.data.strip()
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
		return ''
	
	def visit_HTMLData(self, node):
		return '"{}"'.format(node.data)
	
	def parse_attribute_value(self, value):
		""" Returns an AST for the attribute value
		"""
		ret = []
		state = 'html'
		
		while len(value):
			c = value.pop(0)
			
			if state == 'html':
				if c == '{':
					c2 = value[i + 1]
					if c2 == '{':
						c3 = value[i + 2]
						if c3 == '{':
							state = 'js expression'
							
							i += 3
							continue
		
		
		return ret
