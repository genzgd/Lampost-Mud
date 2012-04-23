function ActionLMModule (root) {
	
	var actionInput = root.find("#actionInput");
	if (lmapp.dialogCount == 0) {
		actionInput.focus();
	}
	actionInput.keydown(sendAction);
	
	function refocus(data) {
		actionInput.focus();
	};

	function sendAction(event) {
		if (event.which != 13) {
			return true;
		}
		event.preventDefault();
		event.stopPropagation();
		event.stopImmediatePropagation();
		
		var action = actionInput.val();
		if (action) {
			lmdp.dispatch("default_line", ">" + action);
			lmdp.dispatchEvent(new LMRemote.Request("action", {action: action}));
			actionInput.val("");
		}
		return false;
	}
	
	this.register("refocus", refocus);
}

ActionLMModule.prototype = LMWeb.BaseModule;