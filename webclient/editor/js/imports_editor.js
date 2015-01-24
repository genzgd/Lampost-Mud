angular.module('lampost_editor').controller('ImportsEditorCtrl', ['$scope', 'lpUtil', 'lpDialog',  function($scope, lpUtil, lpDialog) {


  $scope.setDatabaseDialog = function() {
     lpDialog.show({templateUrl: "editor/dialogs/select_db.html" , controller: "DbSelectorCtrl",
        scope: $scope});
  }
}]);


angular.module('lampost_editor').controller('DbSelectorCtrl', ['$scope', 'lpRemote',  function($scope, lpRemote) {
  $scope.newParams = {db_port: 6379, db_num:0, db_pw: null};
  if ($scope.dbParams) {
    angular.copy($scope.dbParams, $scope.newParams);
  }

  $scope.setDatabase = function() {
    lpRemote.request("editor/imports/set_db", $scope.newParams).then(function(newParams) {
      $scope.dbParams = newParams;
      $scope.dismiss();
    })
  }
}]);
