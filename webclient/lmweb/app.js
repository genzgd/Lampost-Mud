function LMApp() {

	var self = this;
	var mainDiv = null;
	var currentDisplay = {};
	var loginModuleId = -1;
	var actionModuleId = -1;
	var displayModuleId = -1;
	var displayReg = null;
	var sessionErrorDialog = null;
	
	this.dialogCount = 0;
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
			if (data == "invalid_session") {
				if (sessionErrorDialog) {
					sessionErrorDialog.dialog("close");
				}
				sessionErrorDialog = showDialog(1, "Your Session Has Expired", "Session Expired");
			} 
		}
		startLogin();
		self.logged_in = false;
	}
	
	function showDialog(dialog_type, msg, title) {
		posx = (window.innerWidth - 300) / 2;
		pos = [posx, 150];

		dialog = $("<div style='font-size: 10;' title='" + title +
				"'><p align='center'>" + msg + "</p>");
		
		if (dialog_type == 0) {
			buttons = [ {text: "Yes",
					        	click: function() {
					        		closeDialog(dialog);
					        		sendDialogResponse("yes");
					        		}},
					           {text: "No",
			        			click: function() {
					        		closeDialog(dialog);
					        		sendDialogResponse("no");
					        		}}
					          ];
		} else if (dialog_type == 1) {
			buttons = [ {text: "OK",
						click: function() {
							closeDialog(dialog);
						}}];
		} 
		
		dialog.dialog(
			{	buttons:buttons,
				position: pos,
				dialogClass: "no-close",
				closeOnEscape: false,
				modal: true});
		self.dialogCount++;
		return dialog;
	}
	
	function showDialogEvent(event) {
		return showDialog(event.dialog_type, event.dialog_msg, event.dialog_title);
	}
	
	function closeDialog(dialog) {
		dialog.dialog("close");
		self.dialogCount--;
		if (self.dialogCount == 0) {
			lmdp.dispatch("refocus");
		}
	}
	
	function sendDialogResponse(data) {
		dialogResponse = JSON.stringify({response: data});
		responseArg = {response: dialogResponse};
		lmdp.dispatch("server_request", new LMRemote.Request("dialog", responseArg));	
	}
	
	lmdp.register("doc_ready", init, true);
	lmdp.register("player_list_ready", playerListReady);
	lmdp.register("link_connected", startLogin);
	lmdp.register("display_ready", displayReady);
	lmdp.register("login", login);
	lmdp.register("logout", logout);
	lmdp.register("show_dialog", showDialogEvent);
}

var lmapp = new LMApp();