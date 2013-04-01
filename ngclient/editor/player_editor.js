angular.module('lampost_editor').controller('PlayersEditorCtrl', ['$scope', 'lmRemote', 'lmEditor', 'lmDialog', 'lmBus',
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
                        lmDialog.showOk("Error", error.text);
                    })

                })
        };

        function loadPlayers() {
            $scope.ready = false;
            lmRemote.request($scope.editor.url + '/list', null, true).then(function(players) {
                $scope.players = players;
                $scope.ready = true;
            });
        }

    }]);