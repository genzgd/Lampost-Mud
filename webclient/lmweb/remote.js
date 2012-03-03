function LMRemote() {

	var sessionId = 0;
	var reconnectDialog = null;
	var sessionErrorDialog = null;
	var timerValue = null;
	var timerText = null;
	var reconnectTimer = -1;
	
	function request(event) {
		event.args.session_id = sessionId;
		$.ajax ({url: '/' + event.method,
			dataType: 'json',
			type: 'POST',
			cache: false,
			async: true,
			data: event.args,
			beforeSend: function(xhrObj){
				xhrObj.setRequestHeader("Accept","application/json");
				},
			success: serverResult,
			error: function(jqXHR, textStatus, errorThrown) {
				linkFailure(textStatus + " " + errorThrown);
				}
			});
		};
		
	function link(data) {
		request(new LMRemote.Request("link"));
	}
	
	function reconnectNow() {
		if (reconnectTimer != -1) {
			clearTimeout(reconnectTimer);
			reconnectTimer = -1;
		}
		if (sessionId == 0) {
			request(new LMRemote.Request("connect"));
		} else {
			link();
		}
	}
	
	function updateReconnectTimer() {
		timerValue--;
		if (timerValue <= 0) {
			reconnectNow();
		} else {
			reconnectTimer = setTimeout(updateReconnectTimer, 1000);
		}
		timerText.text(timerValue);
	}
			
	function linkFailure(status) {
		lmdp.log("Link stopped: " + status);
		if (reconnectDialog) {
			timerText.text("15");
		} else {
			reconnectDialog = $("<div style='font-size: 10;' title='Reconnecting to Server'>" +
					"<p align='center'>Connection lost.  Error: " + status +
					"  Reconnecting in <span id='timespan'>15</span>" +
					" seconds.</p>");
			reconnectDialog.dialog(
					{dialogClass: "no-close",
					 closeOnEscape: false,
						buttons: [
					           {text: "Reconnect Now",
					        	   click: reconnectNow}],
					 modal: true});
		}
		timerValue = 15;
		timerText = reconnectDialog.find("#timespan");
		reconnectTimer = setTimeout(updateReconnectTimer, 1000);
	}
		
	function linkUpdate(status) {
		if (reconnectDialog) {
			reconnectDialog.dialog("close");
			reconnectDialog = null;
			lmdp.dispatch("link_reconnected");
		}
		
		if (status == "good") {		
			link();
		} else if (status == "no_session") {
			lmdp.dispatch("logout");
			sessionId = 0;
			reconnectNow();
		} else if (status == "no_login") {
			if (!sessionErrorDialog) {
				sessionErrorDialog = $("<div style='font-size: 10;' title='Session Expired'>" +
						"<p align='center'>Your Session Has Expired</p>");
				sessionErrorDialog.dialog(
						{modal: true});
			}
			lmdp.dispatch("logout");
		}	
	}
		
	function serverResult(eventMap) {
		for (var key in eventMap) {
			lmdp.dispatch(key, eventMap[key]);
		}
	}
	
	function connected(data) {
		sessionId = data;
		link();		
		lmdp.dispatch("link_connected");
	}
	
	lmdp.register("connect", connected);
	lmdp.register("link_status", linkUpdate);
	lmdp.register("server_request", request);
}

LMRemote.Request = function(method, args) {
	this.eventType = "server_request";
	this.method = method;
	if (args === undefined) {
		args = {};
	} 
	this.args = args;
};

var lmremote = new LMRemote();