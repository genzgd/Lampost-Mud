angular.module('lampost').service('lmData', ['lmBus', function(lmBus) {

    var maxLines = 1000;
    var self = this;

    self.defaultDisplays = {};

    clear();

    function clear() {

        if (self.editorWindow && !self.editorWindow.closed) {
            self.editorWindow.close();
            delete self.editorWindow;
        }

        self.display = [];
        self.userId = 0;
        self.playerIds = [];
        self.editors = [];
        self.playerId = 0;
        self.playerList = [];
        self.history = [];
        self.historyIx = 0;
        self.editorWindow = null;
        self.userDisplays = {};
    }

    function updateDisplay(display) {
        var lines = display.lines;
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            var lineDisplay = self.userDisplays[line.display] || self.defaultDisplays[line.display];
            if (lineDisplay) {
                if (line.text == 'HRT') {
                    line.style = {height: '2px', backgroundColor: lineDisplay.color, marginTop: '6px', marginBottom: '3px', marginRight: '3px'};
                    line.text = '';
                } else if (line.text == "HRB") {
                    line.style = {height: '2px', backgroundColor: lineDisplay.color, marginTop: '3px', marginBottom: '6px', marginRight: '3px'};
                    line.text = '';
                } else {
                    line.style = {color: lineDisplay.color};
                }
            }
            self.display.push(line);
        }
        if (self.display.length > maxLines) {
            self.display.splice(0, self.display.length - maxLines);
        }
        lmBus.dispatch("display_update", display);
    }

    lmBus.register('client_config', function(data) {
        self.defaultDisplays = data.default_displays;
    });

    lmBus.register("login", function(data) {
        self.editors = data.editors;
        self.userId = data.user_id;
        self.playerIds = data.player_ids;
        self.playerName = data.name;
        self.userDisplays = data.displays;
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