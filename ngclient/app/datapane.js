angular.module('lampost').controller('DataPaneCtrl', ['$scope', '$timeout', 'lmBus', function($scope, $timeout, lmBus) {
    $scope.tabClass = function(tabName) {
        if (tabName == $scope.activeTab) {
            return 'active';
        }
        return '';
    };
    $scope.changeTab = function(tabName) {
        $scope.activeTab = tabName;
        lmBus.dispatch('data_tab_change', tabName);
    };
    $timeout(function() {
        $scope.changeTab('playerList');
    });
}]);


angular.module('lampost').controller('PlayerListCtrl', ['$scope', 'lmData', 'lmBus', 'lmRemote', function($scope, lmData, lmBus, lmRemote) {

    $scope.playerList = [];
    lmBus.register("player_list", function(data) {
        $scope.playerList = data;
    }, $scope);
    lmBus.register("player_login", function(login) {
        if ($scope.playerList[login.id]) {
            return;
        }
        $scope.playerList[login.id] = login.data;
    }, $scope);
    lmBus.register("player_logout", function(logout) {
        delete $scope.playerList[logout.id];
    }, $scope);


    lmBus.register('data_tab_change', function(tabName) {
        if (tabName == 'playerList') {
            lmRemote.registerService('player_list');
        } else {
            lmRemote.unregisterService('player_list');
        }
    })

}]);