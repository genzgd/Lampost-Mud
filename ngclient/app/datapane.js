angular.module('lampost').controller('DataTabsCtrl', ['$scope', '$timeout',
  'lmBus', 'lmData', 'lmRemote', 'lmUtil', function ($scope, $timeout, lmBus, lmData, lmRemote, lmUtil) {

    var tabInfo = [{id: 'status', label: 'Status', include: 'view/status_tab.html'},
      {id: 'playerList', label: 'Player List', include: 'view/player_list_tab.html'},
      {id: 'channel', label: 'Channel', include: "view/channel_tab.html"},
      {id: 'messages', label: 'Messages', include: "view/messages_tab.html"}
    ];

    var tabMap = {};

    angular.forEach(tabInfo, function (tab) {
      tabMap[tab.id] = tab;
    });

    function updateMsgCount() {
      tabMap.messages.label = "Messages (" + $scope.messages.length + ")";
    }

    function sortChannels() {
      $scope.channelMessages = [];
      angular.forEach(lmData.channels, function (msg_list, channel_id) {
        angular.forEach(msg_list, function (msg) {
          msg.id = channel_id;
          lmData.adjustLine(msg, msg.id + "_channel");
          $scope.channelMessages.push(msg);
        })
      });
      lmUtil.descIntSort($scope.channelMessages, 'timestamp');
    }

    function updateTabs() {
      sortChannels();
      $scope.availChannels = lmData.availChannels;
      $scope.tabList = [];
      $scope.messages = lmData.messages;
      $scope.playerList = lmData.playerList;
      updateMsgCount();

      angular.forEach(tabInfo, function (tab) {
        if (lmData.validTabs.indexOf(tab.id) > -1) {
          $scope.tabList.push(tab);
          tab.visible = true;
        } else {
          tab.visible = false;
          if (lmData.activeTab == tab.id) {
            lmData.activeTab = null;
          }
        }
      });

      if (lmData.messages.length > 0) {
        $scope.changeTab(tabMap.messages);
      } else {
        $scope.changeTab($scope.tabList[0]);
      }
    }

    lmBus.register('login', updateTabs, $scope);
    lmBus.register('logout', updateTabs, $scope);
    lmBus.register('status', function(status) {
      if (status.hasOwnProperty('status')) {
        $scope.status = status;
      }
    });
    lmBus.register('new_message', function () {
      updateMsgCount();
      if (tabMap.messages.visible) {
        $scope.changeTab(tabMap.messages);
      }
    }, $scope);

    $scope.tabClass = function (tab) {
      if (tab.id == lmData.activeTab) {
        return 'active';
      }
      return '';
    };
    $scope.changeTab = function (tab) {
      if (tab.id == lmData.activeTab) {
        return;
      }
      if (tab.id == 'playerList') {
        lmRemote.registerService('player_list_service');
      } else if (lmData.activeTab == 'playerList') {
        lmRemote.unregisterService('player_list_service');
      }
      lmData.activeTab = tab.id;
    };

    $scope.playerList = lmData.playerList;
    $timeout(updateTabs);


    lmBus.register("player_list_update", function () {
      if ($scope.playerList != lmData.playerList) {
        $scope.playerList = lmData.playerList;
      }
    }, $scope);
    lmBus.register("channels", sortChannels, $scope);
    lmBus.register("channel", function (msg) {
      lmData.adjustLine(msg, msg.id + "_channel");
      $scope.channelMessages.unshift(msg);
    }, $scope);


    $scope.deleteMessage = function (msg) {
      lmRemote.asyncRequest("messages/delete", {msg_id: msg.msg_id, player_id: lmData.playerId}).then(function () {
        var msg_ix = lmData.messages.indexOf(msg);
        lmData.messages.splice(msg_ix, 1);
        updateMsgCount();
      })
    };

    $scope.msgTime = function (msg) {
      var date = new Date(msg.timestamp * 1000);
      var now = new Date();
      var result = date.toLocaleTimeString();

      if (date.toLocaleDateString() != now.toLocaleDateString()) {
        result += " " + date.toLocaleDateString();
      }
      return result;
    };

    $scope.$on('$destroy', function () {
      if (lmData.activeTab == 'playerList') {
        lmRemote.unregisterService('player_list_service');
      }
      lmData.activeTab = null;
    })
  }]);

angular.module('lampost').controller('FriendReqCtrl', ['$scope', 'lmData', 'lmRemote', function ($scope, lmData, lmRemote) {
  $scope.respond = function (response) {
    lmRemote.asyncRequest("messages/friend_response", {action: response, player_id: lmData.playerId,
      source_id: $scope.msg.content.friend_id, msg_id: $scope.msg.msg_id}).then(function () {
        var msg_ix = lmData.messages.indexOf($scope.msg);
        lmData.messages.splice(msg_ix, 1);
      })
  }
}]);
