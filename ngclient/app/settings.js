angular.module('lampost').controller('SettingsCtrl', ['$scope', 'lmRemote', 'lmDialog', 'lmBus',
    function ($scope, lmRemote, lmDialog, lmBus) {

    $scope.headings = [{id:"account", label:"Account", class:"active"},
        {id:"characters", label:"Characters", class:""},
        {id:"display", label:"Text Display", class:""},
        {id:"notify", label:"Notifications", class:""}];
    $scope.headingId = "account";
    $scope.click = function (headingId) {
        $scope.headingId = headingId;
        for (var i = 0; i < $scope.headings.length; i++) {
            var heading = $scope.headings[i];
            heading.class = headingId == heading.id ? "active" : "";
        }
    };

    $scope.deleteAccount = function() {
        lmDialog.showPrompt({title:"Confirm Account Deletion", prompt:"Account Password: ", password:true,
                submit:function(password) {
                    lmRemote.request("settings/delete_account", {password:password}).then(function(response) {
                        lmDialog.showOk("Account Deleted", "Your account has been deleted");
                        lmBus.dispatchMap(response);
                    });
            }
        });
    };
}]);

angular.module('lampost').controller('AccountFormCtrl', ['$scope', '$timeout', 'lmData', 'lmRemote',
    function ($scope, $timeout, lmData, lmRemote) {
    $scope.nameInUse = false;
    $scope.emailInUse = false;
    $scope.passwordMismatch = false;

    lmRemote.request("settings/get", {user_id:lmData.userId}).then(updateSettings);

    function updateSettings(data) {
        $scope.user = data;
        $scope.user.confirm = "";
        $scope.original_user_name = data.user_name;
    }

    $scope.submitAccount = function() {
        if ($scope.user.confirm != $scope.user.password) {
            $scope.passwordMismatch = true;
        } else {
            lmRemote.request("settings/update_account", {user_id:lmData.userId,
                user:$scope.user}).then(function() {
                    $scope.showSuccess = true;
                    $scope.user.password = "";
                    $scope.user.confirm = "";
                    $timeout(function() {
                        $scope.showSuccess = false;
                    }, 3000);
                }, function(error) {
                    if (error.id == 'NonUnique') {
                        $scope.emailInUse = true;
                    } else {
                        $scope.nameInUse = true;
                    }
                })
        }
    }

}]);

angular.module('lampost').controller('CharactersTabCtrl', ['$scope', 'lmData', 'lmRemote', 'lmBus', 'lmDialog',
    function($scope, lmData, lmRemote, lmBus, lmDialog) {

    $scope.players = [];
    $scope.errorText = null;
    $scope.deleteCharacter = function(playerId) {
        if (playerId == lmData.playerId) {
            $scope.errorText = "Cannot delete logged in player";
            return;
        }
        lmDialog.showPrompt({title:"Delete Player", prompt:"Enter account password to delete player " + playerId + ":", password:true,
            submit: function(password) {
                lmRemote.request("settings/delete_player", {player_id:playerId, password:password}).then(function(players) {
                    $scope.players = players;
                }, function(error) {
                    $scope.errorText = error.text;
                });
            }
        });
    };

    lmBus.register('players_updated', loadCharacters, $scope);

    $scope.addCharacter = function() {
        lmDialog.show({templateUrl:"dialogs/new_character.html", controller:"NewCharacterCtrl"});
    };

    loadCharacters();
    function loadCharacters() {
        lmRemote.request("settings/get_players", {user_id: lmData.userId}).then(function(players) {
            $scope.players = players;
        });
    }


}]);


angular.module('lampost').controller('DisplayTabCtrl', ['$scope', '$timeout', 'lmData', 'lmRemote', function($scope, $timeout, lmData, lmRemote) {

    $scope.selectors = [];
    $scope.showSuccess = false;

    angular.forEach(lmData.defaultDisplays, function(value, key) {
       var selector = {name: key, desc: value.desc, defaultColor:value.color};
       var userDisplay = lmData.userDisplays[key];
       if (userDisplay) {
           selector.userColor = userDisplay.color;
       } else {
           selector.userColor = selector.defaultColor;
       }
       $scope.selectors.push(selector);
    });

    $scope.updateDisplay = function() {
        var newDisplays = {};
        angular.forEach($scope.selectors, function(selector) {
           if (selector.userColor != selector.defaultColor) {
               newDisplays[selector.name] = {color: selector.userColor};
           }
        });
        lmData.userDisplays = newDisplays;
        lmRemote.request("settings/update_display", {displays: newDisplays}).then(function() {
            $scope.showSuccess = true;
            $timeout(function() {$scope.showSuccess = false;}
                , 3000);
            })
    }

}]);

angular.module('lampost').controller('NotifyTabCtrl', ['$scope', 'lmData', 'lmRemote', function($scope, lmData, lmRemote) {

}]);
