angular.module('lampost_mud').controller('NewCharacterCtrl', ['$scope', 'lmData', 'lpRemote', 'lpEvent', 'lpDialog',
  function ($scope, lmData, lpRemote, lpEvent, lpDialog) {

    $scope.playerName = '';
    $scope.errorText = null;
    $scope.activeScreen = 'race';
    $scope.playerData = {};

    lpRemote.request("client_data/new_char").then(function (newCharData) {
      $scope.races = newCharData.races;
      $scope.ready = true;
    });

    $scope.tryCancel = function () {
      if (lmData.playerIds.length == 0) {
        lpDialog.showConfirm("No Characters", "This account has no characters and will be deleted.  Do you still wish to continue?",
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
      lpRemote.request("settings/create_player", {user_id: lmData.userId, player_name: $scope.playerName, player_data: $scope.playerData})
        .then(function () {
          if (!lmData.playerId) {
            lpEvent.dispatch('server_request', 'login', {player_id: $scope.playerName.toLowerCase()});
          }
          lpEvent.dispatch('players_updated');
          $scope.dismiss();
        }, function (error) {
          $scope.errorText = error.text;
        });
    };

  }]);

angular.module('lampost_mud').controller('SelectCharacterCtrl', ['$scope', 'lpRemote', 'lpEvent', 'lmData',
  function ($scope, lpRemote, lpEvent, lmData) {

    $scope.players = [];

    $scope.selectCharacter = function (playerId) {
      lpEvent.dispatch('server_request', 'login', {player_id: playerId});
    };

    lpEvent.register('login', $scope.dismiss, $scope);

    loadCharacters();
    function loadCharacters() {
      lpRemote.request("settings/get_players", {user_id: lmData.userId}).then(function (players) {
        $scope.players = players;
      });
    }
  }]);
