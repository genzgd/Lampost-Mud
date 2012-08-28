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
angular.module('lampost').run(['$rootScope', 'lmRemote', 'lmGame',  function($rootScope, lmRemote, lmGame) {
    $rootScope.$broadcast("server_request", "connect");
}]);

//noinspection JSUnusedGlobalSymbols
function NavController($scope, $location) {

    $scope.links = [{name:"game", label:"Mud", priority:0},
        {name:"account", label:"Account", priority:100}];

    $scope.siteTitle = lampost_config.title;
    $(window).on("resize", function() {
        $scope.$apply(resize);
    });

    $scope.linkClass = function(name) {
        return ($location.path() == '/' + name) ? "active" : "";
    };

    resize();
    function resize() {
        var newHeight = $(window).height() - $('#lm-navbar').height() - 18;
        $scope.mainHeight = {height: newHeight.toString() + "px"};
    }
}

function GameController($scope, lmDialog, lmGame) {
    $scope.$on("logout", function(event, data) {
        lmDialog.removeAll();
        $scope.actionPane = "login";
        if (data == "invalid_session") {
            lmDialog.showOk("Session Expired", "Your session has expired.");
        }
    });
    $scope.actionPane = lmGame.player ? "action" : "login";
    $scope.$on("login", function() {
            $scope.actionPane = "action";
        }
    );
}

//noinspection JSUnusedGlobalSymbols
function LoginController($rootScope, $scope) {
    $scope.email = "";
    $scope.login = function() {
        if ($scope.email) {
            $rootScope.$broadcast("server_request", "login", {user_id: $scope.email});
        }
    };
}

//LoginController

function ActionController($rootScope, $scope, lmGame) {

    var curAction;
    $scope.update = 0;
    $scope.action = "";
    $scope.display = lmGame.display;
    $scope.$on("display_update", function () {
        $scope.display = lmGame.display;
        $scope.update++;
    });
    $scope.sendAction = function () {
        if (this.action) {
            $rootScope.$broadcast("server_request", "action", {action:this.action});
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

