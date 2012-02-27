function DisplayLMModule (root) {
		
	var padding = "00000000";
	var textWindow = root.find("#textWindow");
	
	function defaultLine(text) {
		displayLine({text: text, color: 0});
		scroll();
	};
	
	function displayLine(line) {
		var htmlline = $("<span>" + line.text + "</span>");
		var color = parseInt(line.color).toString(16).toUpperCase();
		color = padding.substring(0, 6-color.length) + color;
		htmlline.attr("style", "color: #" + color);
		textWindow.append(htmlline);
		textWindow.append($("<br />"));
	};

	function scroll () {
		textWindow.scrollTop(textWindow[0].scrollHeight);
	};

	function display(display) {
		lines = display.lines;
		for (var i = 0; i < lines.length; i++) {
			displayLine(lines[i]);
		}
		scroll();		
	};
		
	this.register("display", display);
	this.register("default_line", defaultLine);
	lmdp.dispatch("display_ready");
}

DisplayLMModule.prototype = LMWeb.BaseModule;

