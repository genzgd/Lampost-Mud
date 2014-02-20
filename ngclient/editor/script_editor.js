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
      newModel.dbo_id = $scope.selectedAreaId + ":" + newModel.id;
    };

    $scope.editor.newEdit($scope.editor.editModel);
  }]);

