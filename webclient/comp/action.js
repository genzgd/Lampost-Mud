function ActionLMModule (root) {
	
	var prev_actions = [];
	var history_loc = -1;
	var actionInput = root.find("#actionInput");
	if (lmapp.dialogCount == 0) {
		actionInput.focus();
	}
	actionInput.keydown(sendAction);
	
	function refocus(data) {
		actionInput.focus();
	};

	function sendAction(event) {
		if (event.which == 38) {
			//if 
		}
		
		if (event.which != 13) {
			return true;
		}
		event.preventDefault();
		event.stopPropagation();
		event.stopImmediatePropagation();
		
		var action = actionInput.val();
		if (action) {
			prev_actions.unshift(action);
			history_loc = -1;
			lmdp.dispatch("default_line", ">" + action);
			lmdp.dispatchEvent(new LMRemote.Request("action", {action: action}));
			actionInput.val("");
		}
		return false;
	}
	
	this.register("refocus", refocus);
}

ActionLMModule.prototype = LMWeb.BaseModule;