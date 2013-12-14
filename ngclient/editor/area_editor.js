angular.module('lampost_editor').controller('AreaEditorCtrl', ['$scope', 'lmEditor',
  function($scope, lmEditor) {

    lmEditor.cacheEntry('area');
    lmEditor.prepare(this, $scope).prepareList('area');

  }]);

angular.module('lampost_editor').controller('RoomListCtrl', ['$q', '$scope', 'lmEditor',
  function($q, $scope, lmEditor) {

    var areaId;
    var listKey;

    $scope.editor = $scope.editorMap.room;

    var refresh = lmEditor.prepare(this, $scope).prepareList;

    $scope.$on('updateModel', updateModel);

    function updateModel() {
      if ($scope.model) {
        lmEditor.deref(listKey);
        areaId = $scope.model.dbo_id;
        listKey = "room:" + areaId;
        $scope.areaId = areaId;
        lmEditor.cacheEntry({key: listKey, url: 'room/list/' + areaId, idSort: true});
        refresh(listKey);
      } else {
        $scope.modelList = null;
      }
    }

    this.newDialog = function(newModel) {
      newModel.id = $scope.model.next_room_id;
    };

    this.preCreate = function(newModel) {
      newModel.dbo_id = areaId + ":" + newModel.id;
    };

    this.postCreate = function() {
      // This is a child list editor, so we open the room editor instead of
      // editing in place
      return $q.reject();
    }

  }]);

