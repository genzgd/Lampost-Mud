angular.module('lampost_editor').controller('PlayerEditorCtrl', ['$scope', 'lpEditor',
  function ($scope, lpEditor) {



  }]);


angular.module('lampost_editor').controller('UserEditorCtrl', ['$scope', 'lpEvent', 'lpEditor', 'lpCache',
  function ($scope, lpEvent, lpEditor, lpCache) {

    $scope.editPlayer = function(player_id) {
      var playerModel = lpCache.cacheValue('player:' + player_id);
      if (playerModel) {
        lpEvent.dispatchLater('startEdit', playerModel);
      }
    }


  }]);