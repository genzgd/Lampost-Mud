angular.module('lampost_editor').controller('AreaEditorCtrl', ['$scope', 'lmEditor',
  function($scope, lmEditor) {

    lmEditor.cacheEntry('area');
    lmEditor.prepare(this, $scope).prepareList('area');

  }]);

angular.module('lampost_editor').controller('RoomListCtrl', ['$q', '$scope', 'lmEditor', 'lmBus',
  function($q, $scope, lmEditor, lmBus) {

    var areaId;
    var listKey;

    $scope.editor = {label: "Room", url: "room", create: 'dialog'};

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

    this.postCreate = function(newModel) {
      lmBus.dispatch('start_editor', 'room', newModel);
      return $q.reject();
    };

  }]);

