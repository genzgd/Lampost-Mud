angular.module('lampost_mud').controller('NewCharacterCtrl', ['$scope', 'lpData', 'lpRemote', 'lpEvent', 'lpDialog',
  function ($scope, lpData, lpRemote, lpEvent, lpDialog) {

    $scope.playerName = '';
    $scope.errorText = null;
    $scope.activeScreen = 'race';
    $scope.playerData = {};

    lpRemote.request("new_char_data").then(function (newCharData) {
      $scope.races = newCharData.races;
      $scope.ready = true;
    });

    $scope.tryCancel = function () {
      if (lpData.playerIds.length == 0) {
        lpDialog.showConfirm("No Characters", "This account has no characters and will be deleted.  Do you still wish to continue?").then(
          function () {
            lpRemote.request("settings/delete_account").then(function (response) {
              lpEvent.dispatchMap(response);
            });
            $scope.dismiss();
          });
      } else {
        $scope.dismiss();
      }
    };

    $scope.createCharacter = function () {
      if ($scope.playerName.indexOf(" ") > -1) {
        $scope.errorText = "Spaces not permitted in character names";
        return;
      }
      lpRemote.request("settings/create_player", {user_id: lpData.userId, player_name: $scope.playerName, player_data: $scope.playerData})
        .then(function () {
          if (!lpData.playerId) {
            lpRemote.send('player_login', {player_id: $scope.playerName.toLowerCase()});
          }
          lpEvent.dispatch('players_updated');
          $scope.dismiss();
        }, function (error) {
          $scope.errorText = error.text;
        });
    };

  }]);

angular.module('lampost_mud').controller('SelectCharacterCtrl', ['$scope', 'lpRemote', 'lpEvent', 'lpData',
  function ($scope, lpRemote, lpEvent, lpData) {

    $scope.players = [];

    $scope.selectCharacter = function (playerId) {
      lpRemote.send('player_login', {player_id: playerId});
    };

    lpEvent.register('login', $scope.dismiss, $scope);

    loadCharacters();
    function loadCharacters() {
      lpRemote.request("settings/get_players", {user_id: lpData.userId}).then(function (players) {
        $scope.players = players;
      });
    }
  }]);
