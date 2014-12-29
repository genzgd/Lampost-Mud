angular.module('lampost_editor').controller('PlayerEditorCtrl', ['$scope', 'lpCache', 'lpEditor',
  function ($scope, lpCache, lpEditor) {

    lpCache.cache('race').then(function(races) {
      $scope.races = races;
    });

    $scope.$on('$destroy', function() {
      lpCache.deref('race');
    });


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