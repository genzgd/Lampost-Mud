
angular.module('lampost_editor').service('lpBuildService', ['lmBus', 'lpEditor', function(lmBus, lpEditor) {

  lpEditor.registerContext('area', {create: function(model) {
    model.next_room_id = 1;
  }});

  lpEditor.registerContext('room', {parentType: 'area'});


}]);

angular.module('lampost_editor').controller('BuildViewCtrl', ['$scope', 'lmBus', 'lpBuildService', 'lpEditor',
  function($scope, lmBus, lpBuildService, lpEditor) {

    var editArea = null;

    $scope.activeArea = function() {
      return editArea ? editArea.name : '-NOT SET-';
    };


    $scope.newEditor = function(editorId, event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      lmBus.dispatch('newEdit', editorId);
    }


}]);