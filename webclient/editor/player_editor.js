angular.module('lampost_editor').controller('PlayersEditorCtrl', ['$scope', 'lmEditor',
  function ($scope, lmEditor) {

    var helpers = lmEditor.prepare(this, $scope);

    helpers.prepareList('player');

    $scope.refresh = function() {
      lmEditor.invalidate('player');
      helpers.prepareList('player');
    }

  }]);
