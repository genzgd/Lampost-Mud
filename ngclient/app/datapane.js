angular.module('lampost').controller('DataTabsCtrl', ['$scope', '$timeout', 'lmBus', 'lmData', 'lmRemote', function($scope, $timeout, lmBus, lmData, lmRemote) {

    var tabInfo = {player_list: {id: 'playerList', label: 'Player List', include: 'view/player_list_tab.html'},
                  messages: {id: 'messages', label: 'Messages', include: "view/messages_tab.html"},
                  chat: {id: 'chat', label: 'Chat'}};


    function updateMsgCount() {
        tabInfo.messages.label = "Messages (" + $scope.messages.length + ")";
    }

    function updateTabs() {
        $scope.tabList = [];
        $scope.messages = lmData.messages;
        updateMsgCount();
        angular.forEach(lmData.validTabs, function(tabName) {
            angular.forEach(tabInfo, function(tab) {
                if (tab.id == tabName) {
                    $scope.tabList.push(tab);
                    tab.visible = true;
                } else {
                    tab.visible = false;
                }
            })
        });
        if ($scope.messages.length > 0) {
            $scope.changeTab(tabInfo.messages);
        } else {
            $scope.changeTab($scope.tabList[0]);
        }
    }

    lmBus.register('login', updateTabs, $scope);
    lmBus.register('logout', updateTabs, $scope);
    lmBus.register('new_message', function() {
        updateMsgCount();
        var messageTab = tabInfo.messages;
        if (messageTab.visible) {
            $scope.changeTab(messageTab)
        }
    }, $scope);
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

    $scope.playerList = [];
    $scope.messages = [];
    $timeout(updateTabs);

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

    $scope.deleteMessage = function(msg) {
        lmRemote.asyncRequest("messages/delete", {msg_id: msg.msg_id, player_id: lmData.playerId}).then(function() {
            var msg_ix = lmData.messages.indexOf(msg);
            lmData.messages.splice(msg_ix, 1);
            updateMsgCount();
        })
    };

    $scope.msgTime = function(msg) {
        var date = new Date(msg.timestamp * 1000);
        var now = new Date();
        var result = date.toLocaleTimeString();

        if (date.toLocaleDateString() != now.toLocaleDateString()) {
            result += " " + date.toLocaleDateString();
        }
        return result;
    }
}]);

angular.module('lampost').controller('FriendReqCtrl', ['$scope', 'lmData', 'lmRemote', function($scope, lmData, lmRemote) {
    $scope.respond = function(response) {
        lmRemote.asyncRequest("messages/friend_response", {action: response, player_id: lmData.playerId,
            source_id: $scope.msg.content.friend_id, msg_id:$scope.msg.msg_id}).then(function() {
            var msg_ix = lmData.messages.indexOf($scope.msg);
            lmData.messages.splice(msg_ix, 1);
        })
    }
}]);
