function ActionLMModule (root) {
	
	actionInput = root.find("#actionInput");
	actionInput.focus();
	actionInput.keypress(function (event) {
		if (event.which == 13) {
			return sendAction(event);
		};
	});
	
	function close(data) {
		root.remove();
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
}

ActionLMModule.prototype = LMWeb.BaseModule;