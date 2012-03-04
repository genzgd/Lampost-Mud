function ActionLMModule (root) {
	
	var actionInput = root.find("#actionInput");
	actionInput.focus();
	actionInput.keypress(function (event) {
		if (event.which == 13) {
			return sendAction(event);
		};
	});
	
	function refocus(data) {
		actionInput.focus();
	};

	function sendAction(event) {
		var action = actionInput.val();
		if (action) {
			event.preventDefault();
			lmdp.dispatch("default_line", ">" + action);
			lmdp.dispatchEvent(new LMRemote.Request("action", {action: action}));
			actionInput.val("");
		}
		return false;
	}
	
	this.register("refocus", refocus);
}

ActionLMModule.prototype = LMWeb.BaseModule;