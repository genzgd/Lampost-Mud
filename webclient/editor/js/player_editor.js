angular.module('lampost_editor').controller('PlayerEditorCtrl', ['$scope', 'lpCache', 'lpEditor', 'lpEvent', 'lpEditorTypes',
  function ($scope, lpCache, lpEditor, lpEvent, lpEditorTypes) {

    var prevLevel, model;

    function setPerms() {
      model = $scope.model;
      $scope.canPromote = model.can_write && lpEditor.playerId != model.dbo_id && lpEditor.immLevel >= lpEditor.constants.imm_levels.admin;
      prevLevel = $scope.model.imm_level;
    }

    $scope.checkPromote = function() {
      var error;
      if (model.logged_in == 'Yes') {
        error = "Please do that in game.";
      } else if (lpEditor.immLevel <= model.imm_level && lpEditor.immLevel < lpEditor.constants.imm_levels.supreme) {
        error = "You cannot promote to that level!"
      }
      if (error) {
        $scope.errors.promote = error;
        $scope.model.imm_level = prevLevel;
      } else {
        $scope.errors.promote = null;
        prevLevel = $scope.model.imm_level;
      }
    };

    lpCache.cache('race').then(function(races) {
      $scope.races = races;
    });

    $scope.$on('$destroy', function() {
      lpCache.deref('race');
    });

    lpEvent.register('editReady', setPerms);

    $scope.playerRoomSelect = new lpEditorTypes.ChildSelect('room_id', 'room');

  }]);


angular.module('lampost_editor').controller('UserEditorCtrl', ['$scope', 'lpEvent', 'lpEditor', 'lpCache',
  function ($scope, lpEvent, lpEditor, lpCache) {

    $scope.editPlayer = function(player_id) {
      var playerModel = lpCache.cachedValue('player:' + player_id);
      if (playerModel) {
        lpEvent.dispatchLater('startEdit', playerModel);
      }
    }

  }]);
