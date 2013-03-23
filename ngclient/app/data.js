angular.module('lampost').service('lmData', ['lmBus', function(lmBus) {

    var maxLines = 1000;
    var padding = "00000000";
    var self = this;

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
        self.userColors = {};
        self.defaultColors = {}

    }

    function updateDisplay(display) {
        var lines = display.lines;
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            var color = self.userColors[line.color] || self.defaultColors[line.color];
            if (color) {
                line.style = {color: color.value};
            }
            self.display.push(line);
        }
        if (self.display.length > maxLines) {
            self.display.splice(0, self.display.length - maxLines);
        }
        lmBus.dispatch("display_update", display);
    }

    lmBus.register('client_config', function(data) {
        self.defaultColors = data.default_colors;
    });

    lmBus.register("login", function(data) {
        self.editors = data.editors;
        self.userId = data.user_id;
        self.playerIds = data.player_ids;
        self.playerName = data.name;
        translateColors(data.colors);
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

    function translateColors(colors) {
        angular.forEach(colors,  function(colorData, colorName) {
            var strValue =  parseInt(colorData.value).toString(16).toUpperCase();
            self.colors[colorName] = '#' + padding.substring(0, 6 - strValue.length) + strValue;
        });
    }

}]);

function PlayerListController($scope, lmData, lmBus) {

    lmBus.register("player_list", update, $scope);
    update();

    function update() {
        $scope.playerList = lmData.playerList;
    }
}
PlayerListController.$inject = ['$scope', 'lmData', 'lmBus'];