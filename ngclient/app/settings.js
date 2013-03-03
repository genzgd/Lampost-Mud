angular.module('lampost').controller('SettingsController', ['$scope', 'lmRemote', 'lmDialog',
    function ($scope, lmRemote, lmDialog) {

    $scope.headings = [{id:"account", label:"Account", class:"active"},
        {id:"characters", label:"Characters", class:""}];
       // {id:"colors", label:"Colors", class:""}];
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
                    lmRemote.request("settings/delete_account", {password:password}).then(function() {
                        lmDialog.showOk("Account Deleted", "Your account has been deleted");
                    });
            }
        });
    };
}]);

angular.module('lampost').controller('AccountFormController', ['$scope', '$timeout', 'lmData', 'lmRemote',
    function ($scope, $timeout, lmData, lmRemote) {
    $scope.inUse = false;
    $scope.passwordMismatch = false;

    lmRemote.request("settings/get", {user_id:lmData.player.user_id}).then(updateSettings);

    function updateSettings(data) {
        $scope.user = data;
        $scope.user.confirm = "";
        $scope.original_user_name = data.user_name;
    }

    $scope.submitAccount = function() {
        if ($scope.user.confirm != $scope.user.password) {
            $scope.passwordMismatch = true;
        } else {
            lmRemote.request("settings/update_account", {user_id:lmData.player.user_id,
                user:$scope.user}).then(function() {
                    $scope.showSuccess = true;
                    $scope.user.password = "";
                    $scope.user.confirm = "";
                    $timeout(function() {
                        $scope.showSuccess = false;
                    }, 3000);
                }).error(function() {
                    $scope.inUse = true;
                })
        }
    }

}]);

angular.module('lampost').controller('CharactersTabController', ['$scope', 'lmData', 'lmRemote',
    function($scope, lmData, lmRemote) {



}]);

