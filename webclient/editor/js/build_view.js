
angular.module('lampost_editor').controller('BuildViewController', ['$scope', 'lmBus', 'lmEditor',
  function($scope, lmBus, lmEditor) {

    var editArea = null;
    var selectArea = null;
    var mainEditor = null;

    $scope.activeArea = function() {
      return editArea ? editArea.name : '-NOT SET-';
    };

    $scope.mainBuildInclude = 'editor/view/no-editor.html';

    $scope.newEditor = function(editorId, event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      $scope.mainBuildInclude = 'editor/view/' + editorId + '.html';
    }


}]);