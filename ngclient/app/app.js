var lampost = angular.module('lampost', []);

lampost.config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider) {
    $routeProvider.
        when('/game', {templateUrl: 'view/main.html',   controller: GameController}).
        when('/editor', {templateUrl: 'view/editor.html'}).
        when('/account', {templateUrl: 'view/account.html'}).
        otherwise({redirectTo: '/game'});
}]);

lampost.service('lmLog', function() {
    this.log  = function(msg) {
       if (window.console) {
           window.console.log(msg);
       }
   }
});

lampost.run(['$rootScope', 'lmRemote', 'lmGame',  function($rootScope, lmRemote, lmGame) {
    $rootScope.$broadcast("server_request", "connect");
}]);

function NavController($scope) {
    $(window).on("resize", function() {
        $scope.$apply(resize);
    });

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

function LoginController($rootScope, $scope) {
    $scope.email = "";
    $scope.login = function() {
        if ($scope.email) {
            $rootScope.$broadcast("server_request", "login", {user_id: $scope.email});
        }
    };
}

function ActionController($rootScope, $scope, lmGame) {

    var curAction;
    $scope.update = 0;
    $scope.action = "";
    $scope.display = lmGame.display;
    $scope.$on("display_update", function() {
        $scope.display = lmGame.display;
        $scope.update++;
    })
    $scope.sendAction = function() {
        if (this.action) {
            $rootScope.$broadcast("server_request", "action", {action: this.action});
            lmGame.history.push(this.action);
            lmGame.historyIx = lmGame.history.length;
            this.action = "";
        }
    }
    $scope.historyUp = function() {
        if (lmGame.historyIx > 0) {
            if (lmGame.historyIx == lmGame.history.length) {
                curAction = this.action;
            }
            lmGame.historyIx--;
            this.action = lmGame.history[lmGame.historyIx];
        }
    }
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

