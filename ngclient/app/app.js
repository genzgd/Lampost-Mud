angular.module('lampost', ['lampost_dir', 'lampost_svc']);

angular.module('lampost').config(['$routeProvider', function($routeProvider) {
    $routeProvider.
        when('/game', {templateUrl: 'view/main.html',   controller: GameController}).
        when('/editor', {templateUrl: 'view/editor.html'}).
        when('/account', {templateUrl: 'view/account.html'}).
        otherwise({redirectTo: '/game'});
}]);

// Using here so they get instantiated.
//noinspection JSUnusedLocalSymbols
angular.module('lampost').run(['$rootScope', 'lmBus', 'lmRemote', 'lmGame',  function($rootScope, lmBus, lmRemote, lmGame) {
    window.onbeforeunload = function() {
        window.windowClosing = true;
    };
    $rootScope.siteTitle = lampost_config.title;
    $('title').text(lampost_config.title);
    lmBus.dispatch("server_request", "connect");
}]);


function NavController($rootScope, $scope, $location, lmBus) {

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

    var baseLinks = [new Link("game", "Mud", "icon-leaf", 0),
        new Link("account", "Account", "icon-user", 50)];

    var editor = new Link("editor", "Editor", "icon-wrench", 100);

    function validatePath()  {
        $scope.links = baseLinks.slice();
        for (var i = 0; i < $scope.links.length; i++) {
            if ($scope.links[i].active()) {
                return;
            }
        }
        $location.path('/' + baseLinks[0].name);
    }

    validatePath();
    lmBus.register("login", function(loginData) {
        $rootScope.editors = loginData.editors;
        if (loginData.editors) {
           $scope.links.push(editor);
        }}, $scope);

    lmBus.register("logout", validatePath, $scope);
}
NavController.$inject = ['$rootScope', '$scope', '$location', 'lmBus'];


function GameController($scope, lmDialog, lmGame, lmBus) {
    lmBus.register("logout", function(data) {
        lmDialog.removeAll();
        $scope.actionPane = "login";
        if (data == "invalid_session") {
            lmDialog.showOk("Session Expired", "Your session has expired.");
        }}, $scope);
    $scope.actionPane = lmGame.player ? "action" : "login";
    lmBus.register("login", function() {
            $scope.actionPane = "action";
        }, $scope);

    $(window).on("resize", function() {
        $scope.$apply(resize);
    });

    resize();
    function resize() {
        var newHeight = $(window).height() - $('#lm-navbar').height() - 18;
        $scope.gameHeight = {height: newHeight.toString() + "px"};
    }
}
GameController.$inject = ['$scope', 'lmDialog', 'lmGame', 'lmBus'];


function LoginController($scope, lmRemote, lmDialog) {
    $scope.siteDescription = lampost_config.description;
    $scope.email = "";
    $scope.login = function() {
        if ($scope.email) {
            lmRemote.request("login", {user_id: $scope.email}).then(loginError);
        }
    };

    function loginError(response) {
        if (response == 'not_found') {
            lmDialog.showOk("Player not found", "That player does not exist.");
        }
    }

}
LoginController.$inject = ['$scope', 'lmRemote', 'lmDialog'];


function ActionController($scope, lmBus, lmGame) {
    var curAction;
    $scope.update = 0;
    $scope.action = "";
    $scope.display = lmGame.display;
    lmBus.register("display_update", function () {
        $scope.display = lmGame.display;
        $scope.update++;
    }, $scope);
    $scope.sendAction = function () {
        if (this.action) {
            lmBus.dispatch("server_request", "action", {action:this.action});
            lmGame.history.push(this.action);
            lmGame.historyIx = lmGame.history.length;
            this.action = "";
        }
    };
    $scope.historyUp = function () {
        if (lmGame.historyIx > 0) {
            if (lmGame.historyIx == lmGame.history.length) {
                curAction = this.action;
            }
            lmGame.historyIx--;
            this.action = lmGame.history[lmGame.historyIx];
        }
    };
    $scope.historyDown = function() {
        if (lmGame.historyIx < lmGame.history.length) {
            lmGame.historyIx++;
            if (lmGame.historyIx == lmGame.history.length) {
                this.action = curAction;
            } else {
                this.action = lmGame.history[lmGame.historyIx];
            }
        }
    }
}
ActionController.$inject = ['$scope', 'lmBus', 'lmGame'];

