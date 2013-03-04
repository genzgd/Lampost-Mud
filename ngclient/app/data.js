angular.module('lampost').service('lmData', ['lmBus', function(lmBus) {

    var maxLines = 1000;
    var padding = "00000000";
    var self = this;

    clear();

    function clear() {
        self.display = [];
        self.userId = 0;
        self.playerIds = [];
        self.editors = [];
        self.playerId = 0;
        self.playerList = [];
        self.history = [];
        self.historyIx = 0;
        self.editorWindow = null;
    }

    function updateDisplay(display) {
        var lines = display.lines;
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            var color = parseInt(line.color).toString(16).toUpperCase();
            color = '#' + padding.substring(0, 6-color.length) + color;
            line.style = {color: color};
            self.display.push(line);
        }
        if (self.display.length > maxLines) {
            self.display.splice(0, maxLines - self.display.length);
        }
        lmBus.dispatch("display_update", display);
    }

    lmBus.register("login", function(data) {
        self.editors = data.editors;
        self.userId = data.user_id;
        self.playerIds = data.player_ids;
        self.playerName = data.name;
        self.playerId = self.playerName.toLocaleLowerCase();
        localStorage.setItem("lm_editors_" + self.playerId, JSON.stringify(self.editors));
    }, null, -100);

    lmBus.register("user_login", function(data) {
        self.userId = data.user_id;
        self.playerIds = data.player_ids;
    }, null, -100);

    lmBus.register("player_list", function(data) {
        self.playerList = data;
    });

    lmBus.register("display", updateDisplay, null, -100);
    lmBus.register("logout", clear, null, -100);

}]);

function PlayerListController($scope, lmData, lmBus) {

    lmBus.register("player_list", update, $scope);
    update();

    function update() {
        $scope.playerList = lmData.playerList;
    }
}
PlayerListController.$inject = ['$scope', 'lmData', 'lmBus'];