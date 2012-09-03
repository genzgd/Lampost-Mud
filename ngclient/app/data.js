angular.module('lampost').service('lmData', ['lmBus', function(lmBus) {

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
        self.player = data;}, null, -100);

    lmBus.register("player_list", function(data) {
        self.playerList = data;
    });

    lmBus.register("display", updateDisplay, null, -100);
    lmBus.register("logout", function() {
        self.player = null;
        self.display = [];
        self.history = [];
        self.historyIx = 0;
        }, null, -100);

}]);

function PlayerListController($scope, lmData, lmBus) {

    lmBus.register("player_list", update, $scope);
    update();

    function update() {
        $scope.playerList = lmData.playerList;
    }
}
PlayerListController.$inject = ['$scope', 'lmData', 'lmBus'];