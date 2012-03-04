function LoginLMModule (root) {

	var nameInput = root.find("#nameInput");
	nameInput.focus();
	
	nameInput.keypress(function (event) {	
			var input = $(this);
			if (event.which == 13 && input.val()) {
				event.preventDefault();
				lmdp.dispatchEvent(new LMRemote.Request("login", {"user_id" : input.val()}));
				return false;
			}
			return true;
		});
	
	function refocus() {
		nameInput.focus();
	}
	
	this.register("link_reconnected", refocus);
}

LoginLMModule.prototype = LMWeb.BaseModule;