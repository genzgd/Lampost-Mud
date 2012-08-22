lampost.service('lmDisplay', ['$rootScope', function($rootScope) {

    var displayLines = [];
    var maxLines = 1000;
    var padding = "00000000";

    function updateDisplay(event, display) {
        var lines = display.lines;
        for (var i = 0; i < lines.length; i++) {
            line = lines[i];
            var color = parseInt(line.color).toString(16).toUpperCase();
            color = '#' + padding.substring(0, 6-color.length) + color;
            line.style = {color: color};
            displayLines.push(lines[i]);
        }
        if (lines.length > maxLines) {
            lines.splice(0, maxLines - lines.length);
        }
        $rootScope.$broadcast("display_update", displayLines);
    }

    $rootScope.$on("display", updateDisplay);
    $rootScope.$on("logout", function() {displayLines = []});

}]);