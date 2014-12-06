angular.module('lampost_editor').controller('SocialEditorCtrl', ['$scope', 'lpRemote', 'lpEditor',
  function ($scope, lpRemote, lpEditor) {

    var preview;

    $scope.editMode = true;
    $scope.source = 'Player';
    $scope.target = 'Target';
    $scope.sourceSelf = false;
    $scope.displayMap = {};

    $scope.startEditMode = function() {
      $scope.editMode = true;
      updateDisplayMap();
    }

    $scope.previewSocial = function () {
      lpRemote.request('editor/social/preview', {target: $scope.target, self_source: $scope.sourceSelf,
        source: $scope.source, b_map: $scope.model.b_map})
        .then(function (data) {
          preview = data;
          $scope.editMode = false;
          updateDisplayMap();
        });
    };

    $scope.updateSocial = function(bType) {
      $scope.model.b_map[bType] = $scope.displayMap[bType];
    }

    function updateDisplayMap() {
      angular.forEach(lpEditor.constants.broadcast_types, function(bType) {
        var key = bType.id;
        $scope.displayMap[key] = $scope.editMode ? $scope.model.b_map[key] : preview[key];
      });
    }

    updateDisplayMap();

  }]);

