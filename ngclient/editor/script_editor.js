angular.module('lampost_editor').controller('ScriptListCtrl', ['$q', '$scope', 'lmEditor',
  function ($q, $scope, lmEditor) {

    var listKey;

    $scope.editor = {id: 'script', url: "script",  label: 'Script'};
    var helpers = lmEditor.prepare(this, $scope);

    $scope.$on('updateModel', function () {
      if ($scope.model) {
        lmEditor.deref(listKey);
        listKey = "script:" + $scope.areaId;
        helpers.prepareList(listKey);
      } else {
        $scope.modelList = null;
      }
    });

    this.preCreate = function (newModel) {
      newModel.dbo_id = $scope.areaId + ":" + newModel.dbo_id;
    };

    this.postCreate = function (newModel) {
      $scope.startEditor('script', newModel);
      return $q.reject();
    };

  }]);

angular.module('lampost_editor').controller('ScriptEditorCtrl', ['$q', '$scope', 'lmEditor',
  function ($q, $scope, lmEditor) {

    lmEditor.prepare(this, $scope);

    this.preCreate = function (newModel) {
      newModel.dbo_id = $scope.selectedAreaId + ":" + newModel.dbo_id;
    };

    $scope.editor.newEdit($scope.editor.editModel);

    $scope.approvedClass = function() {
      if ($scope.model && $scope.model.approved) {
        return "badge-success";
      }
      return "badge-warning";
    };

     $scope.approvedText = function() {
      if ($scope.model && $scope.model.approved) {
        return "Approved";
      }
      return "Not Approved";
    };
  }]);

angular.module('lampost_editor').controller('ScriptSelectorCtrl', ['$q', '$scope', function($q, $scope, hostType, host) {
  var noScript = {dbo_id: '--None--'};
  var noItems = {dbo_id: '--No Items--', invalid: true};

  $scope.objType = 'script';
  $scope.hostType = hostType;
  $scope.host = host;

    $scope.areaChange = function() {};
    $scope.listChange = function(rooms) {

      if (rooms.length > 0) {
        $scope.roomList = rooms;
        $scope.hasRoom = true;
      } else {
        $scope.roomList = [{dbo_id: "N/A"}];
        $scope.hasRoom= false;
      }
       $scope.entranceRoom = $scope.roomList[0];
    };


}]);

