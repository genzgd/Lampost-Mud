function LMApp() {

	var self = this;
	var mainDiv = null;
	var currentDisplay = {};
	var loginModuleId = -1;
	var actionModuleId = -1;
	var displayModuleId = -1;
	var displayReg = null;
	var sessionErrorDialog = null;
	
	this.logged_in = false;

	function init() {
		mainDiv = $("#mainDiv");
		currentDisplay.lines = [];
		lmweb.loadModule("playerlist", mainDiv.find("#playerList"));
	}
	
	function playerListReady(data) {
		lmdp.dispatchEvent(new LMRemote.Request("connect"));
	}
	
	function startLogin(data) {
		// Capture all the display output here until the main display is ready
		if (loginModuleId == -1) {
			displayReg = lmdp.register("display", updateDisplay);
			loginModuleId = lmweb.loadModule("login", mainDiv.find("#displayPane"));
		}
	}
	
	function login(data) {
		lmweb.unloadModule(loginModuleId);
		loginModuleId = -1;
		displayModuleId = lmweb.loadModule("display", mainDiv.find("#displayPane"));
		actionModuleId = lmweb.loadModule("action", mainDiv.find("#actionPane"));
	}
		
	function updateDisplay(display) {
		currentDisplay.lines = currentDisplay.lines.concat(display.lines);
	}
	
	function displayReady(data) {
		// Send the display lines to the real display panel
		lmdp.unregister(displayReg);
		lmdp.dispatch("display", currentDisplay);
		currentDisplay.lines = [];
		self.logged_in = true;
	}
	
	function logout(data) {
		if (actionModuleId != -1) {
			lmweb.unloadModule(actionModuleId);
			lmweb.unloadModule(displayModuleId);
			actionModuleId = -1;
			displayModuleId = -1;
			if (data == "invalid_session" && !sessionErrorDialog) {
				sessionErrorDialog = $("<div style='font-size: 10;' title='Session Expired'>" +
					"<p align='center'>Your Session Has Expired</p>");
					sessionErrorDialog.dialog(
						{modal: true,
						 close: function() {
							 sessionErrorDialog = null;
							 lmdp.dispatch("refocus");
						 }});
			}
		}
		self.logged_in = false;
		startLogin();
	}
	
	lmdp.register("doc_ready", init, true);
	lmdp.register("player_list_ready", playerListReady);
	lmdp.register("link_connected", startLogin);
	lmdp.register("display_ready", displayReady);
	lmdp.register("login", login);
	lmdp.register("logout", logout);
}

var lmapp = new LMApp();