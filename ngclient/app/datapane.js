angular.module('lampost').controller('DataPaneCtrl', ['$scope', '$timeout', 'lmBus', 'lmData', 'lmRemote', function($scope, $timeout, lmBus, lmData, lmRemote) {


    var tabInfo = [{id: 'playerList', label: 'Player List', include: 'view/player_list_tab.html'},
        {id: 'messages', label: 'Messages', include: "view/messages_tab.html"},
        {id: 'globalChannel', label: 'Gossip'}];

    function updateTabs() {
        $scope.tabList = [];
        angular.forEach(lmData.validTabs, function(tabName) {
            angular.forEach(tabInfo, function(tab) {
                if (tab.id == tabName) {
                    $scope.tabList.push(tab);
                }
            })
        });
        $scope.changeTab($scope.tabList[0]);
    }

    lmBus.register('login', updateTabs, $scope);
    lmBus.register('logout', updateTabs, $scope);
    $scope.tabClass = function(tab) {
        if (tab == $scope.activeTab) {
            return 'active';
        }
        return '';
    };
    $scope.changeTab = function(tab) {
        if (tab == $scope.activeTab) {
            return;
        }
        if (tab.id == 'playerList') {
            lmRemote.registerService('player_list');
        } else if ($scope.activeTab && $scope.activeTab.id == 'playerList') {
            lmRemote.unregisterService('player_list');
        }
        $scope.activeTab = tab;
    };
    $timeout(updateTabs);

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
}]);
