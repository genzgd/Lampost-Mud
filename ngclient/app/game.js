lampost.service('lmGame', ['$rootScope', function($rootScope) {

    var maxLines = 1000;
    var padding = "00000000";
    var self = this;

    this.display = [];
    this.player = null;
    this.playerList = [];
    this.history = [];
    this.historyIx = 0;

    function updateDisplay(event, display) {
        var lines = display.lines;
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            var color = parseInt(line.color).toString(16).toUpperCase();
            color = '#' + padding.substring(0, 6-color.length) + color;
            line.style = {color: color};
            self.display.push(lines[i]);
        }
        if (self.display.length > maxLines) {
            self.display.splice(0, maxLines - self.display.length);
        }
        $rootScope.$broadcast("display_update", display);
    }

    $rootScope.$on("login", function(event, data) {
        self.player = data;
    });

    $rootScope.$on("player_list", function(event, data) {
        self.playerList = data;
    });

    $rootScope.$on("display", updateDisplay);
    $rootScope.$on("logout", function() {
        self.player = null;
        self.display = [];
        self.history = [];
        self.historyIx = 0;
        });

}]);

function PlayerListController($scope, lmGame) {

    $scope.$on("player_list", update);
    update();

    function update() {
        $scope.playerList = lmGame.playerList;
    }
}