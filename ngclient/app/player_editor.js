angular.module('lampost_edit').controller('PlayersEditorController', ['$scope', 'lmRemote', 'lmEditor', 'lmDialog', 'lmBus',
    function ($scope, lmRemote, lmEditor, lmDialog, lmBus) {

        lmBus.register("editor_activated", function(editor) {
            if (editor == $scope.editor) {
                loadPlayers();
            }
        });

        $scope.deletePlayer = function(index) {
            var player = $scope.players[index];
            lmDialog.showConfirm("Confirm Delete",
                "Are you sure you want to delete " + player.id + "?", function() {
                    lmRemote.request($scope.editor.url + "/delete", {player_id:player.id}, true).then(function() {
                        $scope.players.splice(index, 1);
                    }, function(error) {
                        if (error.status == 409) {
                            lmDialog.showOk("Error", error.data);
                        }
                    })

                })
        };

        function loadPlayers() {
            $scope.ready = false;
            lmRemote.request($scope.editor.url + '/list').then(function(players) {
                $scope.players = players;
                $scope.ready = true;
            });
        }

    }]);