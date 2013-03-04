angular.module('lampost').controller('NewCharacterController', ['$scope', 'lmData', 'lmRemote', 'lmBus', function($scope, lmData, lmRemote, lmBus) {

    $scope.playerName = "";
    $scope.errorText = null;
    $scope.playerData = {};

    $scope.tryCancel = function() {
        $scope.dismiss();
    };

    $scope.createCharacter = function() {
        if ($scope.playerName.indexOf(" ") > -1) {
            $scope.errorText = "Spaces not permitted in character names";
            return;
        }
        lmRemote.request("settings/create_player", {user_id:lmData.userId,  player_name:$scope.playerName, player_data:$scope.playerData})
            .then(function() {
            if (!lmData.playerId) {
                lmBus.dispatch('server_request', 'login', {player_id:$scope.playerName.toLowerCase()});
            }
            $scope.dismiss()
        }).error(function(error) {
            $scope.errorText = error;
        });
    }

}]);
