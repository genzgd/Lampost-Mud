angular.module('lampost_editor').controller('SocialEditorCtrl', ['$scope', 'lpRemote', 'lpEditor', 'lpEvent',
  function ($scope, lpRemote, lpEditor, lpEvent) {

    var preview = {};
    var bTypeIds = [];
    var sourceSelf = false;

    $scope.bTypeGrid = [];

    angular.forEach(lpEditor.constants.broadcast_types, function(bType) {
      $scope.bTypeGrid[bType.grid_x] = $scope.bTypeGrid[bType.grid_x] || [];
      $scope.bTypeGrid[bType.grid_x][bType.grid_y] = bType;
      bTypeIds.push(bType.id);
      });

    $scope.editMode = true;
    $scope.source = 'Player';
    $scope.target = 'Target';
    $scope.displayMap = {};

    $scope.startEditMode = function() {
      $scope.editMode = true;
      updateDisplayMap();
    }

    $scope.toggleTarget = function() {
      sourceSelf = !sourceSelf;
      $scope.targetTitle = sourceSelf ? "Target is self." : 'Target is other.';
      $scope.targetClass = 'fa ' + (sourceSelf ? 'fa-reply-all' : 'fa-long-arrow-right')
    }

    $scope.previewSocial = function () {
      lpRemote.request('editor/social/preview', {target: $scope.target, self_source: sourceSelf,
        source: $scope.source, b_map: $scope.model.b_map})
        .then(function (data) {
          preview = data;
          preview.dbo_id = $scope.model.dbo_id
          $scope.editMode = false;
          updateDisplayMap();
        });
    };

    $scope.updateSocial = function(bType) {
      $scope.model.b_map[bType] = $scope.displayMap[bType];
    }

    function updateDisplayMap() {
      if ($scope.model.b_map) {
        angular.forEach(bTypeIds, function(key) {
          $scope.displayMap[key] = $scope.editMode ? $scope.model.b_map[key] : preview[key];
        });
      }
    }

    lpEvent.register('editReady', function() {
      if (!$scope.editMode &&  $scope.model.dbo_id != preview.dbo_id) {
        $scope.previewSocial()
      } else {
        updateDisplayMap()
      }
    }, $scope);

    updateDisplayMap();
    $scope.toggleTarget();

  }]);

