angular.module('lampost_editor').service('EditorHelper', ['$q', 'lmBus', 'lmRemote', 'lmEditor', 'lmDialog', 'lmUtil',
  function ($q, lmBus, lmRemote, lmEditor, lmDialog, lmUtil) {

    this.prepare = function (controller, $scope) {

      var newDialogId = null;
      var originalObject = null;
      var editor = $scope.editor;
      var baseUrl = 'editor/' + editor.url + '/';

      $scope.objectExists = false;
      $scope.newModel = null;
      $scope.copyFromId = null;
      $scope.objLabel = editor.id.charAt(0).toUpperCase() + editor.id.slice(1);

      $scope.$watch('model', function () {
        $scope.isDirty = !angular.equals(originalObject, $scope.model);
      }, true);

      function intercept(interceptor, args) {
        if (controller[interceptor]) {
          return $q.when(controller[interceptor](args));
        }
        return $q.when();
      }

      function mainDelete(object) {
        intercept('preDelete').then(function () {
          lmRemote.request(baseUrl + 'delete', {dbo_id: object.dbo_id}).then(function () {
            if ($scope.model = object) {
              $scope.model = null;
            }
            for (var i = 0; i < $scope.modelList.length; i++) {
              if ($scope.modelList[i] == object) {
                $scope.modelList.splice(i, 1);
                break;
              }
            }
            intercept('postDelete', object);
          });
        })
      }

      $scope.revertObject = function () {
        $scope.model = angular.copy(originalObject);
        $scope.$broadcast('updateModel');
      };

      $scope.updateObject = function () {
        intercept('preUpdate').then(function () {
          lmRemote.request(baseUrl + 'update', $scope.model).then(
            function (updatedObject) {
              $scope.isDirty = false;
              for (var i = 0; i < $scope.modelList.length; i++) {
                if ($scope.modelList[i].dbo_id == updatedObject.dbo_id) {
                  $scope.modelList[i] = updatedObject;
                  break;
                }
              }
              intercept('postUpdate', updatedObject).then(function () {
                $scope.editObject(updatedObject);
              })
            }
          )
        })
      };

      $scope.submitNewObject = function () {
        intercept('preCreate', $scope.newModel).then(function () {
          lmRemote.request(baseUrl + 'create', $scope.newModel).then(
            function (createdObject) {
              $scope.modelList.push(createdObject);
              lmUtil.stringSort($scope.modelList, 'dbo_id');
              lmDialog.close(newDialogId);
              intercept('postCreate', createdObject).then(function() {
                 $scope.editObject(createdObject);
              });
            }, function () {
              $scope.newExists = true;
            });
        })
      };

      $scope.newObjectDialog = function () {
        $scope.newModel = {};
        intercept('newDialog').then(function() {
           var dialogName = editor.create === 'dialog' ? editor.id : 'generic';
           newDialogId = lmDialog.show({templateUrl: 'editor/dialogs/new_' + dialogName + '.html', scope: $scope.$new()});
        });
      };

      $scope.newModelInclude = function() {
        return editor.create === 'fragment' ? 'editor/fragments/new_' + editor.id + '.html' : null;
      };

      $scope.editObject = function (object) {
        originalObject = object;
        $scope.model = angular.copy(originalObject);
        intercept('startEdit', $scope.model).then(function () {
          $scope.$broadcast('updateModel');
        });
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
        $scope.newModel = angular.copy(object);
        delete $scope.newModel.dbo_id;
        var dialogName = editor.copyDialog ? editor.id : 'generic';
        newDialogId = lmDialog.show({templateUrl: 'editor/dialogs/copy_' + dialogName + '.html', scope: $scope.$new()});
      };

      $scope.objectRowClass = function (object) {
        return ($scope.model && $scope.model.dbo_id == object.dbo_id) ? 'highlight' : '';
      };

      return function() {
        intercept('preLoad').then(function () {
          $q.all([
              lmEditor.cache(controller.modelList).then(function (modelList) {
                if (modelList) {
                  $scope.modelList = modelList;
                }
              }),
              lmEditor.cache(controller.model).then(function (model) {
                if (model) {
                  $scope.editObject(model);
                }
              })
            ])
            .then(function () {
              intercept('onLoaded').then(function () {
                $scope.ready = true;
              })
            });
        });
      };

    }
  }
]);

angular.module('lampost_editor').controller('EffectListController', ['$scope', function ($scope) {

  $scope.$on('updateModel', updateModel);

  function updateModel() {
    if ($scope.$parent.model) {
      $scope.calcValues = $scope.$parent.model[$scope.calcWatch];
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
      element.scope().$watch(attrs.lmEffectList, function () {
        angular.extend(scope, element.scope().$eval(attrs.lmEffectList));
      })
    }
  }
}]);

angular.module('lampost_editor').controller('SimpleListController', ['$scope', function ($scope) {

  $scope.$on('updateModel', updateModel);

  function updateModel() {
    if ($scope.$parent.model) {
      $scope.selectValues = $scope.$parent.model[$scope.selectWatch];
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

  updateModel();

}]);

angular.module('lampost_editor').directive('lmSimpleList', [function () {
  return {
    restrict: 'A',
    scope: {},
    templateUrl: 'editor/view/simple_list.html',
    controller: 'SimpleListController',
    link: function (scope, element, attrs) {
      element.scope().$watch(attrs.lmSimpleList, function () {
        angular.extend(scope, element.scope().$eval(attrs.lmSimpleList));
      })
    }
  }
}]);


angular.module('lampost_editor').controller('AttrListController', ['$scope', function ($scope) {

  $scope.$on('updateModel', updateModel);

  function updateModel() {
    if ($scope.$parent.model) {
      $scope.attrValues = $scope.$parent.model[$scope.attrWatch];
    }
  }

  updateModel();
}]);


angular.module('lampost_editor').directive('lmAttrList', [function () {
  return {
    restrict: 'A',
    scope: {},
    templateUrl: 'editor/view/attr_list.html',
    controller: 'AttrListController',
    link: function (scope, element, attrs) {
      element.scope().$watch(attrs.lmAttrList, function () {
        angular.extend(scope, element.scope().$eval(attrs.lmAttrList));
      });
    }
  }
}]);

