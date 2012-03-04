function PlayerlistLMModule (root) {
		
	var tableBody = root.find("#playerTableBody");
	
	function display(players) {
		tableBody.empty();
		for (var name in players) {
			info = players[name];
			var row = $("<tr><td>" + name + "</td><td>" + info.status + "</td><td>" +
					info.loc + "</td></tr>");
			tableBody.append(row);
		}
	};
			
	this.register("player_list", display);
	lmdp.dispatch("player_list_ready");

}

PlayerlistLMModule.prototype = LMWeb.BaseModule;
