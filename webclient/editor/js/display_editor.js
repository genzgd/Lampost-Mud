angular.module('lampost_editor').controller('DisplayEditorCtrl', ['$scope', 'lmRemote', 'lmBus', function ($scope, lmRemote) {

  $scope.updateDisplays = function () {
    lmRemote.request('editor/display/update', {displays: $scope.displays}, true);
  };

  lmRemote.request('editor/display/list').then(function (displays) {
    $scope.displays = displays;
    $scope.ready = true;
  })

}]);
