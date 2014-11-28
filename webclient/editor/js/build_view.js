
angular.module('lampost_editor').controller('BuildViewController', ['$scope', 'lmBus', 'lpEditor',
  function($scope, lmBus, lpEditor) {

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
      lpEditor.startNew(editorId).then(function () {
        $scope.mainBuildInclude = 'editor/view/' + editorId + '.html';
      });
    }


}]);