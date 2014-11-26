angular.module('lampost_editor').controller('SocialsEditorCtrl', ['$scope', 'lmRemote', 'lmEditor', 'lmDialog',
  function ($scope, lmRemote, lmEditor, lmDialog) {

    var helpers = lmEditor.prepare(this, $scope);
    helpers.prepareList('social');

    $scope.displayMode = 'edit';
    $scope.source = 'Player';
    $scope.target = 'Target';
    $scope.sourceSelf = false;

    $scope.changeSocial = function () {
      $scope.newModel.b_map.s = "You " + $scope.newModel.dbo_id.toLocaleLowerCase() + ".";
      $scope.dialog.newExists = false;
    };

    this.newDialog = function (newModel) {
      newModel.b_map = {};
    };

    $scope.previewSocial = function () {
      lmRemote.request('editor/social/preview', {target: $scope.target, self_source: $scope.sourceSelf,
        source: $scope.source, b_map: $scope.model.b_map})
        .then(function (preview) {
          $scope.preview = preview;
          $scope.displayMode = 'view';
        });
    };


  }]);

