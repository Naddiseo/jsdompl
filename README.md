jsdompl
=======


Input:

```html

<a href="{{ url('foo') }}" >{{ tag }}</a>

```

(Current) Output (from main_old.py)

```javascript


define([], function() {
	var C = document.createElement;
	var T = document.createTextNode;
	function TPL() {
		var $root = document.createDocumentFragment();
		var $text_node0 = T("\n");
		
		var _a0 = C('a');
		
		var $text_node2 = T("\n");
		
		_a0.setAttribute("href",  url('foo') );
		var $text_node1 = T("{{ tag }}");
		_a0.appendChild($text_node1);
		$root.appendChild($text_node0);
		$root.appendChild(_a0);
		$root.appendChild($text_node2);
		return $root;
	}
	return TPL;
});

```

Input2:

```html
<!-- require({'jquery' : '$', 'underscore' : '_'}) -->
<!-- globals('url', 'mylist', 'var_name') -->
<br>
<a href="{{ url('foo') }}" > {{ var_name }}</a>
<div class="list-display">
	{% _.each(mylist, function(idx, item) { %}
		<div class="list-item-{{idx}}"> {{{ item }}}</div>
	{% }); %}
</div>


```

Current output:

```javascript

var $$root0 = F();
var $$text0 = "\n" + "\n" + "\n";

var $$br0 = C("br");

var $$text1 = "\n";

var $$a1 = C("a");
var $$text2 = " " + escape($_var_name);
$$a1.appendChild($$text2);
$$root0.appendChild($$a1);
var $$root1 = F();
var $$text3 = escape($_url('foo'));
$$root1.appendChild($$text3);
$$a1.setAttribute("href", $$root1);

var $$text4 = "\n";

var $$div2 = C("div");
var $$text5 = "\n	";

$__.$_each($_mylist, function($_idx, $_item) {
	var $$div3 = C("div");
var $$text6 = " " + $_item;
	$$div3.appendChild($$text6);
	$$div2.appendChild($$div3);
	var $$root2 = F();
var $$text7 = escape($_idx);
	$$root2.appendChild($$text7);
$$div3.setAttribute("class", $$root2);

	var $$text8 = "\n	";

	
});$$div2.appendChild($$text5);
$$div2.appendChild($$text8);
$$root0.appendChild($$div2);
var $$root3 = F();
$$div2.setAttribute("class", $$root3);

var $$text9 = "\n";
$$root0.appendChild($$text0);
$$root0.appendChild($$br0);
$$root0.appendChild($$text1);
$$root0.appendChild($$text4);
$$root0.appendChild($$text9);


```


Eventual output:

```javascript

define(['jquery', 'underscore'], function($, _) {
	var C = document.createElement;
	var T = document.createTextNode;
	var F = document.createDocumentFragment;
	function TPL(url, mylist, var_name) {
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

```