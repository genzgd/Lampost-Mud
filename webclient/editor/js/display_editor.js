angular.module('lampost_editor').controller('DisplayEditorCtrl', ['$scope', 'lpRemote', 'lpEvent', function ($scope, lpRemote) {

  $scope.updateDisplays = function () {
    lpRemote.request('editor/display/update', {displays: $scope.displays}, true);
  };

  lpRemote.request('editor/display/list').then(function (displays) {
    $scope.displays = displays;
    $scope.ready = true;
  })

}]);
