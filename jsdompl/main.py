from __future__ import unicode_literals, division, absolute_import, print_function

__author__ = "richard"
__created__ = "Jun 28, 2013"

from jsdompl.template import JSDomTemplate

tpl = JSDomTemplate("""
<a href="{{ url('foo') }}" > {{ var_name }}</a>
<div class="list-display">
	{% _.each(mylist, function(idx, item) { %}
		<div class="list-item-{{idx}}"> {{{ item }}}</div>
	{% }); %}
</div>
""")

"""
define(['jquery', 'underscore'], function($, _) {
	var C = document.createElement;
	var T = document.createTextNode;
	var F = document.createDocumentFragment;
	function TPL(url, var_name) {
		var $root0 = F();
		var $a0 = C('a');
		var $text0 = T('\n');
		var $text1 = T(' ');
		var $div0 = C('div');
		var $text2 = T('\n\t');
		var $text3 = T('\n');
		
		$root.appendChild($a0);
		$root.appendChild($text0);
		$root.appendChild($div0);
		$root.appendChild($text3);
		
		$a0.appendChild($text1);
		
		var $tmp0 = url('foo');
		$a0.setAttribute("href", $tmp0);
		
		var $tmp1 = _.escape(var_name);
		$text1.data += $tmp1;
		
		$div0.appendChild($text2);
		
		$div0.className = 'list-display';
		
		_.each(mylist, function(idx, item) {
			var $root1 = F();
			var $text4 = T('\n\t\t');
			var $div1 = C('div');
			var $text5 = T(' ');
			var $text6 = T('\n\t');
			
			$root1.appendChild($text4);
			$root1.appendChild($div1);
			$root1.appendChild($text6);
			
			$div1.appendChild($text5);
			
			var $tmp2 = _.escape(idx);
			var $tmp3 = "list-item-" + $tmp2;
			$div1.className = $tmp4;
			
			var $tmp4 = item;
			$text5.data += $tmp4;
			
			$div0.appendChild($root1);
		});
		
		return $root0;
	}
	return TPL;
});
"""


"""
This is the version of the template that needs to be passed into a javascript
parser so that the required variable names can be found.

var $t0 = "<a href=\"" + _.escape( url('foo') ) + "\" > " + _.escape( var_name ) + "</a>\n" +
"<div class=\"list-display\">" +
"    "; _.each(mylist, function(idx, item) { var $t1 = "\n" +
"        <div class=\"list-item-" + _.escape(idx)"\"> " + item + "</div>\n" +
"    "; }); var $t2 = "\n" +
"</div>";

"""
