angular.module('lampost').controller('NewCharacterController', ['$scope', 'lmData', 'lmRemote', 'lmBus', 'lmDialog',
    function($scope, lmData, lmRemote, lmBus, lmDialog) {

    $scope.playerName = '';
    $scope.errorText = null;
    $scope.playerData = {sex: 'select', size: 'select'};

    $scope.tryCancel = function() {
        if (lmData.playerIds.length == 0) {
            lmDialog.showConfirm("No Characters", "This account has no characters and will be deleted.  Do you still wish to continue?",
                function() {
                    lmRemote.request("settings/delete_account", {}, function(response) {
                        lmBus.dispatchMap(response);
                    });
                    $scope.dismiss();
                });
        } else {
            $scope.dismiss();
        }
    };



    $scope.createCharacter = function() {
        if ($scope.playerData.sex == 'select') {
            $scope.errorText = "Please choose your sex.";
            return;
        }
        if ($scope.playerData.size == 'select') {
            $scope.errorText = "Please choose your size.";
            return;
        }
        if ($scope.playerName.indexOf(" ") > -1) {
            $scope.errorText = "Spaces not permitted in character names";
            return;
        }
        lmRemote.request("settings/create_player", {user_id:lmData.userId,  player_name:$scope.playerName, player_data:$scope.playerData})
            .then(function() {
            if (!lmData.playerId) {
                lmBus.dispatch('server_request', 'login', {player_id:$scope.playerName.toLowerCase()});
            }
            lmBus.dispatch('players_updated');
            $scope.dismiss();
        }, function(error) {
            $scope.errorText = error.data;
        });
    }

}]);

angular.module('lampost').controller('SelectCharacterController', ['$scope', 'lmRemote', 'lmBus', 'lmData',
    function($scope, lmRemote, lmBus, lmData) {

    $scope.players = [];

    $scope.selectCharacter = function(playerId) {
        lmBus.dispatch('server_request', 'login', {player_id:playerId});
    };

    lmBus.register('login', $scope.dismiss, $scope);

    loadCharacters();
    function loadCharacters() {
        lmRemote.request("settings/get_players", {user_id: lmData.userId}, true).then(function(players) {
            $scope.players = players;
        });
    }
}]);
