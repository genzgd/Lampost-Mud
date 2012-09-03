function SettingsController($scope) {

    $scope.headings = [{id:"account", label:"Account", class:"active"},
        {id:"colors", label:"Colors", class:""}];
    $scope.headingId = "account";
    $scope.click = function (headingId) {
        $scope.headingId = headingId;
        for (var i = 0; i < $scope.headings.length; i++) {
            var heading = $scope.headings[i];
            heading.class = headingId == heading.id ? "active" : "";
        }
    };
}
SettingsController.$inject = ['$scope'];


function AccountFormController($scope, $timeout, lmData, lmRemote) {
    $scope.inUse = false;
    $scope.passwordMismatch = false;

    lmRemote.request("settings/get", {user_id:lmData.player.user_id}).then(updateSettings);

    function updateSettings(data) {
        $scope.user = data;
        $scope.user.confirm = "";
        $scope.original_user_name = data.user_name;
    }

    function checkResponse(data) {
        switch (data)
        {
            case "success":
                $scope.showSuccess = true;
                $scope.user.password = "";
                $scope.user.confirm = "";
                $timeout(function() {
                    $scope.showSuccess = false;
                }, 3000);
                break;
            case "name_in_use":
                $scope.inUse = true;
                break;
            default:
        }
    }

    $scope.submitAccount = function() {
        if ($scope.user.confirm != $scope.user.password) {
            $scope.passwordMismatch = true;
        } else {
            lmRemote.request("settings/update_account", {user_id:lmData.player.user_id,
                user:$scope.user}).then(checkResponse)
        }
    }



}
AccountFormController.$inject = ['$scope', '$timeout', 'lmData', 'lmRemote'];

