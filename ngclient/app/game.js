angular.module('lampost').service('lmGame', ['lmBus', function(lmBus) {

    var maxLines = 1000;
    var padding = "00000000";
    var self = this;

    this.display = [];
    this.player = null;
    this.playerList = [];
    this.history = [];
    this.historyIx = 0;

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
        self.player = data;
    });

    lmBus.register("player_list", function(data) {
        self.playerList = data;
    });

    lmBus.register("display", updateDisplay);
    lmBus.register("logout", function() {
        self.player = null;
        self.display = [];
        self.history = [];
        self.historyIx = 0;
        });

}]);

function PlayerListController($scope, lmGame, lmBus) {

    lmBus.register("player_list", update, $scope);
    update();

    function update() {
        $scope.playerList = lmGame.playerList;
    }
}
PlayerListController.$inject = ['$scope', 'lmGame', 'lmBus'];