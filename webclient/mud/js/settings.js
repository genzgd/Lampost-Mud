angular.module('lampost_mud').controller('SettingsCtrl', ['$scope', '$timeout', 'lpRemote', 'lpDialog', 'lpEvent', 'lpData',
  function ($scope, $timeout, lpRemote, lpDialog, lpEvent, lpData) {

    $scope.headings = [
      {id: "general", label: "General", class: "btn-primary"},
      {id: "characters", label: "Characters", class: "btn-default"},
      {id: "display", label: "Text Display", class: "btn-default"},
      {id: "notify", label: "Notifications", class: "btn-default"}
    ];
    $scope.headingId = "general";
    $scope.click = function (headingId) {
      $scope.headingId = headingId;
      for (var i = 0; i < $scope.headings.length; i++) {
        var heading = $scope.headings[i];
        heading.class = headingId == heading.id ? "btn-primary" : "btn-default";
      }
    };

    $scope.deleteAccount = function () {
      lpDialog.showPrompt({title: "Confirm Account Deletion", prompt: "Account Password: ", password: true,
        submit: function (password) {
          lpRemote.request("settings/delete_account", {password: password}).then(function (response) {
            lpDialog.showOk("Account Deleted", "Your account has been deleted");
            lpEvent.dispatchMap(response);
          });
        }
      });
    };

    $scope.nameInUse = false;
    $scope.emailInUse = false;
    $scope.passwordMismatch = false;

    lpRemote.request("settings/get_account", {user_id: lpData.userId}).then(updateSettings);

    function updateSettings(data) {
      $scope.user = data;
      $scope.user.confirm = "";
      $scope.accountName = data.user_name.toUpperCase();
    }

    $scope.submitAccount = function () {
      if ($scope.user.confirm != $scope.user.password) {
        $scope.accountError = "Passwords do not match";
        return;
      }
      if ($scope.user.password && $scope.user.password.length < 4) {
        $scope.accountError = "Password is too short";
        return;
      }
      if ($scope.user.password && $scope.user.password.length > 20) {
        $scope.accountError = "Password is too long";
        return;
      }
      if ($scope.user.user_name.length < 4) {
        $scope.accountError = "Account name is too short.";
        return;
      }
      lpRemote.request("settings/update_account", {user_id: lpData.userId,
        user_update: $scope.user}).then(function () {
        $scope.showSuccess = true;
        $scope.user.password = "";
        $scope.user.confirm = "";
        $scope.accountName = $scope.user.user_name.toUpperCase();
        $timeout(function () {
          $scope.showSuccess = false;
        }, 3000);
      }, function (error) {
        if (error.id == 'NonUnique') {
          $scope.emailInUse = true;
        } else {
          $scope.nameInUse = true;
        }
      })
    }


  }]);

angular.module('lampost_mud').controller('CharactersTabCtrl', ['$scope', 'lpData', 'lpRemote', 'lpEvent', 'lpDialog',
  function ($scope, lpData, lpRemote, lpEvent, lpDialog) {

    $scope.players = [];
    $scope.errorText = null;
    $scope.deleteCharacter = function (playerId) {
      if (playerId == lpData.playerId) {
        $scope.errorText = "Cannot delete logged in player";
        return;
      }
      lpDialog.showPrompt({title: "Delete Player", prompt: "Enter account password to delete player " + playerId + ":", password: true,
        submit: function (password) {
          lpRemote.request("settings/delete_player", {player_id: playerId, password: password}).then(function (players) {
            $scope.players = players;
          }, function (error) {
            $scope.errorText = error.text;
          });
        }
      });
    };

    lpEvent.register('players_updated', loadCharacters, $scope);

    $scope.addCharacter = function () {
      lpDialog.show({templateUrl: "mud/dialogs/new_character.html", controller: "NewCharacterCtrl"});
    };

    loadCharacters();
    function loadCharacters() {
      lpRemote.request("settings/get_players", {user_id: lpData.userId}).then(function (players) {
        $scope.players = players;
      });
    }


  }]);


angular.module('lampost_mud').controller('DisplayTabCtrl', ['$scope', '$timeout', 'lpData', 'lpRemote', function ($scope, $timeout, lpData, lpRemote) {

  $scope.selectors = [];
  $scope.showSuccess = false;

  angular.forEach(lpData.defaultDisplays, function (value, key) {
    var selector = {name: key, desc: value.desc, defaultColor: value.color};
    var userDisplay = lpData.userDisplays[key];
    if (userDisplay) {
      selector.userColor = userDisplay.color;
    } else {
      selector.userColor = selector.defaultColor;
    }
    $scope.selectors.push(selector);
  });

  $scope.updateDisplay = function () {
    var newDisplays = {};
    angular.forEach($scope.selectors, function (selector) {
      if (selector.userColor != selector.defaultColor) {
        newDisplays[selector.name] = {color: selector.userColor};
      }
    });
    lpData.userDisplays = newDisplays;
    lpRemote.request("settings/update_display", {displays: newDisplays}).then(function () {
      $scope.showSuccess = true;
      $timeout(function () {
          $scope.showSuccess = false;
        }
        , 3000);
    })
  }

}]);

angular.module('lampost_mud').controller('NotifyTabCtrl', ['$scope', '$timeout', 'lpEvent', 'lpData', 'lpRemote', function ($scope, $timeout, lpEvent, lpData, lpRemote) {

  $scope.showSuccess = false;
  $scope.isImm = lpData.immLevel;
  $scope.notifies = {friendSound: false, friendDesktop: false, friendEmail: false, allSound: false, allDesktop: false, allEmail: false};
  angular.forEach(lpData.notifies, function (value) {
    $scope.notifies[value] = true;
  });
  $scope.desktopAvailable = window.webkitNotifications && true;
  $scope.updateNotifies = function () {
    var newNotifies = [];
    angular.forEach($scope.notifies, function (value, key) {
      if (value) {
        newNotifies.push(key);
      }
    });
    lpRemote.request('settings/notifies', {notifies: newNotifies}).then(function () {
      $scope.showSuccess = true;
      lpData.notifies = newNotifies;
      $timeout(function () {
        $scope.showSuccess = false;
      }, 3000);
      lpEvent.dispatch('notifies_updated');
    })
  }

}]);
