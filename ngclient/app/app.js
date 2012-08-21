var lampost = angular.module('lampost', []);

lampost.service('lmLog', function() {
    this.log  = function(msg) {
       if (window.console) {
           window.console.log(msg);
       }
   }
});

lampost.run(['$rootScope', 'lmRemote',  function($rootScope, lmRemote) {
    $rootScope.$broadcast("server_request", "connect");
}]);

function LoginController($scope, $rootScope, $templateCache, $http, lmDialog) {
    $scope.loginText = "Login dammit";
    $scope.clickme = function() {
        lmDialog.show({templateUrl: "dialogs/reconnect.html", controller: function(){}});
    };
}

function MainController($scope) {
    $scope.actionText = "Action dammit";
}

function TestController($scope) {

}

