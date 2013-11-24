angular.module('lampost_editor').service('EditorHelper', ['$q', 'lmRemote', 'lmEditor', 'lmDialog', 'lmUtil',
  function ($q, lmRemote, lmEditor, lmDialog, lmUtil) {

    this.prepareScope = function (controller, $scope) {

      var newDialogId = null;
      var originalObject = null;
      var dialogScope = null;
      var editor = $scope.editor;
      var baseUrl = editor.url + '/';

      $scope.ready = false;
      $scope.isDirty = false;
      $scope.objectExists = false;
      $scope.activeObject = null;
      $scope.newObject = null;
      $scope.copyFromId = null;
      $scope.objLabel = editor.id.charAt(0).toUpperCase() + editor.id.slice(1);
      loadObjects();

      $scope.$watch('activeObject', function() {
        $scope.isDirty = !angular.equals(originalObject, $scope.activeObject);
      }, true);

      function intercept(interceptor, args) {
        if (interceptor) {
          return interceptor(args);
        }
        return $q.when();
      }

      function loadObjects() {
        lmRemote.request(baseUrl + 'list').then(function (objects) {
          $scope.objectList = objects;
          $scope.ready = true;
          controller.onLoaded && controller.onLoaded();
        })
      }

      function mainDelete(object) {
        if (controller.preDelete && !controller.preDelete(object)) {
          return;
        }
        lmRemote.request(baseUrl + 'delete', {dbo_id: object.dbo_id}).then(function () {
          if ($scope.activeObject = object) {
            $scope.activeObject = null;
          }
          for (var i = 0; i < $scope.objectList.length; i++) {
            if ($scope.objectList[i] == object) {
              $scope.objectList.splice(i, 1);
              break;
            }
          }
          controller.postDelete && controller.postDelete(object);
        });
      }

      $scope.revertObject = function () {
        $scope.activeObject = angular.copy(originalObject);
        $scope.$broadcast('updateActive');
      };

      $scope.updateObject = function () {
        intercept(controller.preUpdate).then(function () {
          lmRemote.request(baseUrl + 'update', {dbo: $scope.activeObject}).then(
            function (updatedObject) {
              $scope.isDirty = false;
              for (var i = 0; i < $scope.objectList.length; i++) {
                if ($scope.objectList[i].dbo_id == updatedObject.dbo_id) {
                  $scope.objectList[i] = updatedObject;
                  break;
                }
              }
              controller.postUpdate && controller.postUpdate(updatedObject);
            }
          )
        })
      };

      $scope.submitNewObject = function () {
        controller.preCreate && controller.preCreate($scope.newObject);
        lmRemote.request(baseUrl + 'create', {dbo_id: $scope.newObject.dbo_id, dbo: $scope.newObject.dbo}).then(
          function (createdObject) {
            $scope.objectList.push(createdObject);
            lmUtil.stringSort($scope.objectList, 'dbo_id');
            lmDialog.close(newDialogId);
            $scope.editObject(createdObject);
            controller.postCreate && controller.postCreate(createdObject);
          }, function () {
            dialogScope.objectExists = true;
          });
      };

      $scope.newObjectDialog = function () {
        $scope.newObject = {dbo_id: '', dbo: {}};
        var dialogName = $scope.editor.newDialog ? $scope.editor.id : 'generic';
        dialogScope = $scope.$new();
        newDialogId = lmDialog.show({templateUrl: 'editor/dialogs/new_' + dialogName + '.html', scope: dialogScope});
      };

      $scope.editObject = function (object) {
        originalObject = object;
        $scope.activeObject = angular.copy(originalObject);
        controller.startEdit && controller.startEdit();
        $scope.$broadcast('updateActive');
      };

      $scope.deleteObject = function (event, object) {
        event.preventDefault();
        event.stopPropagation();
        lmDialog.showConfirm("Delete " + $scope.objLabel, "Are you certain you want to delete " + $scope.objLabel + " " + object.dbo_id + "?",
          function () {
            mainDelete(object);
          });
      };

      $scope.copyObject = function (event, object) {
        event.preventDefault();
        event.stopPropagation();
        $scope.copyFromId = object.dbo_id;
        $scope.newObject = {dbo_id: '', dbo: angular.copy(object)};
        delete $scope.newObject.dbo['dbo_id'];
        dialogScope = $scope.$new();
        var dialogName = $scope.editor.copyDialog ? $scope.editor.id : 'generic';
        newDialogId = lmDialog.show({templateUrl: 'controller/dialogs/copy_' + dialogName + '.html', scope: dialogScope});
      };

      $scope.objectRowClass = function (object) {
        if ($scope.activeObject && $scope.activeObject.dbo_id == object.dbo_id) {
          return 'highlight';
        }
        return "";
      };
    }
  }
]);


angular.module('lampost_editor').controller('GenEditorCtrl', ['$scope', 'EditorHelper', function ($scope, EditorHelper) {

  EditorHelper.prepareScope(this, $scope);

}]);

angular.module('lampost_editor').controller('EffectListController', ['$scope', function ($scope) {

  $scope.$on('updateActive', updateActive);

  function updateActive() {
    if ($scope.$parent.activeObject) {
      $scope.calcValues = $scope.$parent.activeObject[$scope.calcWatch];
      updateUnused();
    }
  }

  function updateUnused() {
    $scope.unusedValues = [];
    angular.forEach($scope.calcDefs, function (value, key) {
      if (!$scope.calcValues.hasOwnProperty(key)) {
        if ($scope.unusedValues.length === 0) {
          $scope.newId = key;
        }
        $scope.unusedValues.push(key);
      }
    });
  }

  $scope.deleteRow = function (rowId) {
    delete $scope.calcValues[rowId];
    updateUnused();
  };

  $scope.addRow = function () {
      $scope.calcValues[$scope.newId] = 1;
      updateUnused();
  };

}]);

angular.module('lampost_editor').directive('lmEffectList', [function () {
  return {
    restrict: 'A',
    scope: {},
    templateUrl: 'editor/view/effect_list.html',
    controller: 'EffectListController',
    link: function (scope, element, attrs) {
      angular.extend(scope, element.scope().$eval(attrs.lmEffectList));
    }
  }
}]);

angular.module('lampost_editor').controller('SimpleListController', ['$scope', function ($scope) {

  $scope.$on('updateActive', updateActive);

  function updateActive() {
    if ($scope.$parent.activeObject) {
      $scope.selectValues= $scope.$parent.activeObject[$scope.selectWatch];
      updateUnused();
    }
  }

  function updateUnused() {
    $scope.unusedValues = [];
    angular.forEach($scope.selectDefs, function (value, key) {
      if ($scope.selectValues.indexOf(key) === -1) {
        if ($scope.unusedValues.length === 0) {
          $scope.newSelection = key;
        }
        $scope.unusedValues.push(key);
      }
    });
  }

  $scope.deleteRow = function (selection) {
    var ix = $scope.selectValues.indexOf(selection);
    $scope.selectValues.splice(ix, 1);
    updateUnused();
  };

  $scope.addRow = function () {
      $scope.selectValues.push($scope.newSelection);
      updateUnused();
  };

}]);

angular.module('lampost_editor').directive('lmSimpleList', [function () {
  return {
    restrict: 'A',
    scope: {},
    templateUrl: 'editor/view/simple_list.html',
    controller: 'SimpleListController',
    link: function (scope, element, attrs) {
      angular.extend(scope, element.scope().$eval(attrs.lmSimpleList));
    }
  }
}]);

