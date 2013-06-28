from __future__ import absolute_import, division, print_function, unicode_literals

__author__ = "Richard Eames <reames@asymmetricventures.com"
__date__ = "Jun 26, 2013"

from htmlparser import Parser

p = Parser(b"""
<!DOCTYPE html>
<!--  comment- -->
<html>
<body>
	<a href="{{ url("index:home") }}">{{ url_name }}</a>
</body>
</html>
""")
print(p.root())
