var lampost = angular.module('lampost', []);

lampost.service('lmLog', function() {
    this.log  = function(msg) {
       if (window.console) {
           window.console.log(msg);
       }
   }
});

lampost.run(['$rootScope', 'lmRemote', 'lmDisplay',  function($rootScope, lmRemote, lmDisplay) {
    $rootScope.$broadcast("server_request", "connect");
}]);

function LoginController($rootScope, $scope) {
    $scope.email = "";
    $scope.login = function() {
        if ($scope.email) {
            $rootScope.$broadcast("server_request", "login", {user_id: $scope.email});
        }
    };
}

function NavController($scope, $timeout, lmDialog) {
    $(window).on("resize", function() {
        $scope.$apply(resize);
    });
    resize();

    $scope.$on("logout", function(event, data) {
        lmDialog.removeAll();
        $scope.actionPane = "login";
        if (data == "invalid_session") {
            lmDialog.showOk("Session Expired", "Your session has expired.");
        }
    });
    $scope.actionPane = "login";
    $scope.$on("login", function() {
            $scope.actionPane = "action";
        }
    );

    function resize() {
        var newHeight = $(window).height() - $('#lm-navbar').height();
        $scope.mainHeight = {height: newHeight.toString() + "px"};
    }
}

function ActionController($rootScope, $scope) {
    $scope.update = 0;
    $scope.action = "";
    $scope.display = [];
    $scope.$on("display_update", function(event, display) {
        $scope.display = display;
        $scope.update++;
    })
    $scope.sendAction = function() {
        if (this.action) {
            $rootScope.$broadcast("server_request", "action", {action: $scope.action});
            this.action = "";
        }
    }
}

