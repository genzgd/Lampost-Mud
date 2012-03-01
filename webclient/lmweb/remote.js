function LMRemote() {

	var sessionId = 0;
	
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
				stopLink(textStatus + " " + errorThrown);
				}
			});
		};
		
	function link(data) {
		request(new LMRemote.Request("link"));
	}
		
	function stopLink(status) {
		lmdp.log("Link stopped: " + status);
		lmdp.dispatch("link_failure", status);
	}
		
	function linkUpdate(status) {
		if (status == "good") {
			link();
		} else {
			stopLink(status);
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