function LMDispatch() {

	var self = this;
	var listenerMap = {};
	var nextRegId = 0;
	
	this.register = function (type, callback, once) {
			var listeners = listenerMap[type];
			if (!listeners) {
				listeners = {};
				listenerMap[type] = listeners;
			}
			console.log("Registering " + type);
			var regId = nextRegId++;
			var reg = new LMDispatch.Reg(regId, type, callback, once);
			listeners[regId] = reg;
			return reg;
		};
	
	this.unregister = function (reg) {
			var listeners = listenerMap[reg.event_type];
			if (listeners) {
				delete listeners[reg.regId];
			}
		};
	
	this.dispatch = function(type, data) {
			var listeners = listenerMap[type];
			if (listeners) {
				for (var regId in listeners) {
					var reg = listeners[regId];
					reg.callback(data, reg);
					if (reg.once) {
						delete listeners[regId];
					}
				}
				console.log("Event dispatched: " + type + " data: " +  data);
			}
		};
		
	this.dispatchEvent = function (event) {
			self.dispatch(event.eventType, event, event.once);
		};
}

LMDispatch.Reg = function(regId, event_type, callback, once) {
	this.regId = regId;
	this.event_type = event_type;
	this.callback = callback;
	this.once = once === undefined ? false : once;
};

var lmdp = new LMDispatch();
	