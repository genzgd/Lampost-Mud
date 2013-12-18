angular.module('lampost_editor').controller('AreaEditorCtrl', ['$scope', 'lmEditor',
  function ($scope, lmEditor) {

    lmEditor.prepare(this, $scope).prepareList('area');

  }]);


angular.module('lampost_editor').controller('RoomListCtrl', ['$q', '$scope', 'lmEditor', 'lmBus',
  function ($q, $scope, lmEditor, lmBus) {

    var listKey;

    $scope.editor = {id: 'room', url: "room", create: 'dialog', label: 'Room'};

    var refresh = lmEditor.prepare(this, $scope).prepareList;

    $scope.$on('updateModel', function () {
      if ($scope.model) {
        lmEditor.deref(listKey);
        $scope.areaId = $scope.model.dbo_id;
        listKey = "room:" + $scope.areaId;
        refresh(listKey);
      } else {
        $scope.modelList = null;
      }
    });

    this.newDialog = function (newModel) {
      newModel.id = $scope.model.next_room_id;
    };

    this.preCreate = function (newModel) {
      newModel.dbo_id = $scope.areaId + ":" + newModel.id;
    };

    this.postCreate = function (newModel) {
      lmBus.dispatch('start_editor', 'room', newModel);
      return $q.reject();
    };

  }]);


angular.module('lampost_editor').controller('MobileListCtrl', ['$q', '$scope', 'lmEditor', 'lmBus',
  function ($q, $scope, lmEditor, lmBus) {

    var listKey;

    $scope.editor = {id: 'mobile', url: "mobile", create: 'dialog', label: 'Mobile'};
    var refresh = lmEditor.prepare(this, $scope).prepareList;

    $scope.$on('updateModel', function () {
      if ($scope.model) {
        lmEditor.deref(listKey);
        $scope.areaId = $scope.model.dbo_id;
        listKey = "mobile:" + $scope.areaId;
        refresh(listKey);
      } else {
        $scope.modelList = null;
      }
    });

    this.newDialog = function(newModel) {
      newModel.level = 1;
    };

    this.preCreate = function (newModel) {
      newModel.dbo_id = $scope.areaId + ":" + newModel.id;
    };

    this.postCreate = function (newModel) {
      lmBus.dispatch('start_editor', 'mobile', newModel);
      return $q.reject();
    };

  }]);

angular.module('lampost_editor').controller('MobileEditorCtrl', ['$scope', 'lmEditor', function($scope, lmEditor) {
  lmEditor.prepare(this, $scope);
  this.postDelete = function(model) {
      $scope.startEditor('area');
    };

  $scope.editor.newEdit($scope.editor.editModel);
}]);
