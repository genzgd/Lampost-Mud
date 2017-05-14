angular.module('lampost_editor').controller('MainAdminCtrl', ['$scope', 'lpRemote', 'lpUtil',
  function($scope, lpRemote, lpUtil) {

  lpRemote.request('admin/operations', {name: 'list'}).then(function(operations) {
    lpUtil.stringSort(operations, 'name');
    $scope.operations = operations;
  });

  $scope.blanks = function(op) {
    var blanks = [];
    for (var ix = 0; ix < 4 - op.args.length; ix++) {
      blanks.push(ix);
    }
    return blanks;
  };

  $scope.executeOp = function(op) {
    lpRemote.request('admin/operations', op).then(function(result) {
      $scope.operationResult = result ? result : 'No Content';
    })
  };

}]);
