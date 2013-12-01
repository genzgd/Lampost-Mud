angular.module('lampost_editor').controller('AreaEditorCtrl', ['$scope', 'EditorHelper',
  function($scope, EditorHelper) {

    this.modelList = 'area';

    EditorHelper.prepare(this, $scope)();

  }]);

angular.module('lampost_editor').controller('RoomListCtrl', ['$scope', 'EditorHelper',
  function($scope, EditorHelper) {

    var self = this;

    $scope.editor = $scope.editorMap.room;

    var refresh = EditorHelper.prepare(this, $scope);

    $scope.$on('updateModel', updateModel);

    function updateModel() {
      if ($scope.model) {
        var areaId = $scope.model.dbo_id;
        self.modelList = {key: 'rooms:' + areaId, url: 'room/list/' + areaId};
        refresh();
      } else {
        $scope.modelList = null;
      }
    }

  }]);

