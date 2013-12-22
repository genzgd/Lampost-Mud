angular.module('lampost_editor').controller('PlayersEditorCtrl', ['$scope', 'lmEditor',
  function ($scope, lmEditor) {

    lmEditor.prepare(this, $scope).prepareList('player');

  }]);
