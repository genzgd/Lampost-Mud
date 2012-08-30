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
    window.onbeforeunload = function() {
      $rootScope.windowClosing = true;
    };
    $rootScope.siteTitle = lampost_config.title;
    $('title').text($rootScope.siteTitle);
    $rootScope.$broadcast("server_request", "connect");
}]);


function NavController($scope, $location) {
    var baseLinks = [{name:"game", label:"Mud", priority:0},
        {name:"account", label:"Account", priority:50}];

    function validatePath()  {
        $scope.links = baseLinks.slice();
        for (var i = 0; i < baseLinks.length; i++) {
            if ($location.path() == '/' + name) {
                return;
            }
        }
        $location.path('/' + baseLinks[0].name);
    }

    validatePath();
    $scope.$on("login", function(event, loginData) {
        $scope.editors = loginData.editors;
        if (loginData.editors) {
           $scope.links.push({name:"editor", label:"Editor", priority:100});
        }
});

    $scope.$on("logout", function() {
        validatePath();
    });

    $scope.linkClass = function(name) {
        return ($location.path() == '/' + name) ? "active" : "";
    };


}
NavController.$inject = ['$scope', '$location'];


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

    $(window).on("resize", function() {
        $scope.$apply(resize);
    });

    resize();
    function resize() {
        var newHeight = $(window).height() - $('#lm-navbar').height() - 18;
        $scope.gameHeight = {height: newHeight.toString() + "px"};
    }
}
GameController.$inject = ['$scope', 'lmDialog', 'lmGame'];


function LoginController($rootScope, $scope) {
    $scope.email = "";
    $scope.login = function() {
        if ($scope.email) {
            $rootScope.$broadcast("server_request", "login", {user_id: $scope.email});
        }
    };
}
LoginController.$inject = ['$rootScope', '$scope'];


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
ActionController.$inject = ['$rootScope', '$scope', 'lmGame'];

