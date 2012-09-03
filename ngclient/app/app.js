angular.module('lampost', ['lampost_dir', 'lampost_svc']);

angular.module('lampost').config(['$routeProvider', function($routeProvider) {
    $routeProvider.
        when('/game', {templateUrl: 'view/main.html',   controller: GameController}).
        when('/editor', {templateUrl: 'view/editor.html'}).
        when('/settings', {templateUrl: 'view/settings.html'}).
        otherwise({redirectTo: '/game'});
}]);


// Using here so they get instantiated.
//noinspection JSUnusedLocalSymbols
angular.module('lampost').run(['$rootScope', 'lmBus', 'lmRemote', 'lmData', 'lmDialog',
    function($rootScope, lmBus, lmRemote, lmData, lmDialog) {
    window.onbeforeunload = function() {
        window.windowClosing = true;
    };

    $rootScope.siteTitle = lampost_config.title;
    $('title').text(lampost_config.title);

    lmBus.dispatch("server_request", "connect");
}]);




function NavController($scope, $location, lmBus, lmData) {

    function Link(name, label, icon, priority) {
        this.name = name;
        this.label = label;
        this.icon = icon;
        this.priority = priority;
        this.active = function () {
            return $location.path() == '/' + this.name;
        };
        this.class = function() {
            return this.active() ? "active" : "";
        };
        this.iconClass = function() {
            return this.icon + " icon-white" + (this.active() ? "" : " icon-gray");
        };
    }

    var baseLinks = [new Link("game", "Mud", "icon-leaf", 0)];
    var settingsLink =  new Link("settings", "Settings", "icon-user", 50);

    var editorLink = new Link("editor", "Editor", "icon-wrench", 100);

    function validatePath()  {
        $scope.welcome = 'Please Log In';
        $scope.links = baseLinks.slice();
        for (var i = 0; i < $scope.links.length; i++) {
            if ($scope.links[i].active()) {
                return;
            }
        }
        $location.path('/' + baseLinks[0].name);
    }

    validatePath();
    lmBus.register("login", function() {
        if (lmData.player.editors.length) {
            $scope.links.push(editorLink);
        }
        $scope.links.push(settingsLink);
        $scope.welcome = 'Welcome ' + lmData.player.name;
    }, $scope);

    lmBus.register("logout", validatePath, $scope);
}
NavController.$inject = ['$scope', '$location', 'lmBus', 'lmData'];


function GameController($scope, lmBus, lmData) {

    update();
    resize();

    lmBus.register("login", update, $scope);
    lmBus.register("logout", update, $scope);
    $(window).on("resize", function() {
        $scope.$apply(resize);
    });


    function resize() {
        var newHeight = $(window).height() - $('#lm-navbar').height() - 18;
        $scope.gameHeight = {height: newHeight.toString() + "px"};
    }
    function update() {
        $scope.actionPane = lmData.player ? "action" : "login";
    }
}
GameController.$inject = ['$scope', 'lmBus', 'lmData'];


function LoginController($scope, lmRemote) {
    $scope.loginError = false;
    $scope.siteDescription = lampost_config.description;
    $scope.login = function() {
        lmRemote.request("login", {user_id: this.userId,
           password:this.password}).then(loginError);

    };

    function loginError(response) {
        if (response == "not_found") {
            $scope.loginError = true;
        }
    }

}
LoginController.$inject = ['$scope', 'lmRemote'];


function ActionController($scope, lmBus, lmData) {
    var curAction;
    $scope.update = 0;
    $scope.action = "";
    $scope.display = lmData.display;
    lmBus.register("display_update", function () {
        $scope.display = lmData.display;
        $scope.update++;
    }, $scope);
    $scope.sendAction = function () {
        if (this.action) {
            lmBus.dispatch("server_request", "action", {action:this.action});
            lmData.history.push(this.action);
            lmData.historyIx = lmData.history.length;
            this.action = "";
        }
    };
    $scope.historyUp = function () {
        if (lmData.historyIx > 0) {
            if (lmData.historyIx == lmData.history.length) {
                curAction = this.action;
            }
            lmData.historyIx--;
            this.action = lmData.history[lmData.historyIx];
        }
    };
    $scope.historyDown = function() {
        if (lmData.historyIx < lmData.history.length) {
            lmData.historyIx++;
            if (lmData.historyIx == lmData.history.length) {
                this.action = curAction;
            } else {
                this.action = lmData.history[lmData.historyIx];
            }
        }
    }
}
ActionController.$inject = ['$scope', 'lmBus', 'lmData'];

