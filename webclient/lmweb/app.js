function LMApp() {

	var mainDiv = null;
	var currentDisplay = {};
	var loginModuleId = -1;
	var actionModuleId = -1;
	var displayModuleId = -1;
	var displayReg = null;
	
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
		displayReg = lmdp.register("display", updateDisplay);
		loginModuleId = lmweb.loadModule("login", mainDiv.find("#displayPane"));
	}
	
	function login(data) {
		lmweb.unloadModule(loginModuleId);
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
	}
	
	function logout(data) {
		lmweb.unloadModule(actionModuleId);
		lmweb.unloadModule(displayModuleId);
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