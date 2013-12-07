angular.module('lampost_editor').controller('AreaEditorCtrl', ['$scope', 'EditorHelper',
  function($scope, EditorHelper) {

    this.modelList = 'area';

    EditorHelper.prepare(this, $scope)();


  }]);

angular.module('lampost_editor').controller('RoomListCtrl', ['$q', '$scope', 'EditorHelper',
  function($q, $scope, EditorHelper) {

    var self = this;

    $scope.editor = $scope.editorMap.room;

    var refresh = EditorHelper.prepare(this, $scope);

    $scope.$on('updateModel', updateModel);

    function updateModel() {
      if ($scope.model) {
        var areaId = $scope.model.dbo_id;
        $scope.areaId = areaId;
        self.modelList = {key: 'rooms:' + areaId, url: 'room/list/' + areaId};
        refresh();
      } else {
        $scope.modelList = null;
      }
    }

    this.newDialog = function() {
      $scope.newModel.id = $scope.model.next_room_id;
    };

    this.postCreate = function() {
      // This is a child list editor, so we open the room editor instead of
      // editing in place
      $q.reject();
    }

  }]);

