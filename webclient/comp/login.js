function LoginLMModule (root) {

	var nameInput = root.find("#nameInput");
	if (lmapp.dialogCount == 0) {
		nameInput.focus();
	}
	
	nameInput.keypress(function (event) {	
			var input = $(this);
			if (event.which == 13 && input.val()) {
				event.preventDefault();
				event.stopPropagation();
				event.stopImmediatePropagation();
				lmdp.dispatchEvent(new LMRemote.Request("login", {"user_id" : input.val()}));
				input.val("");
				return false;
			}
			return true;
		});
	
	function refocus() {
		nameInput.focus();
	}
	
	
	this.register("refocus", refocus);
}

LoginLMModule.prototype = LMWeb.BaseModule;