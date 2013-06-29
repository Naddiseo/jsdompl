from __future__ import unicode_literals, division, absolute_import, print_function

import re

__author__ = "Richard Eames <reames@asymmetricventures.com>"
__created__ = "Jun 28, 2013"


_whitespace_only_re = re.compile('^[ \t]+$', re.MULTILINE)
_leading_whitespace_re = re.compile('(^[ \t]*)(?:[^ \t\n])', re.MULTILINE)
def indent_text(text, level):
	margin = None
	text = _whitespace_only_re.sub('', text)
	indents = _leading_whitespace_re.findall(text)
	for indent in indents:
		if margin is None:
			margin = indent
		
		# Current line more deeply indented than previous winner:
		# no change (previous winner is still on top).
		elif indent.startswith(margin):
			pass
		
		# Current line consistent with and no deeper than previous winner:
		# it's the new winner.
		elif margin.startswith(indent):
			margin = indent
		
		# Current line and previous winner have no common whitespace:
		# there is no margin.
		else:
			margin = ""
			break
	
	# sanity check (testing/debugging only)
	if 0 and margin:
		for line in text.split("\n"):
			assert not line or line.startswith(margin), \
				   "line = %r, margin = %r" % (line, margin)
	
	if margin:
		if level > len(margin):
			tabs = level - len(margin)
			text = re.sub(r'(?m)^', '\t' * tabs, text)
	else:
		text = re.sub(r'(?m)^', '\t' * level, text)
	return text
