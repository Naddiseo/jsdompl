jsdompl
=======


Input:

```python

<a href="{{ url('foo') }}" >{{ tag }}</a>

```

(Current) Output

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