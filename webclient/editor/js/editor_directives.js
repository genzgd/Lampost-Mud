angular.module('lampost_editor').directive('lpEditList', ['lpEditorView',  function(lpEditorView) {

  return {
    controller: 'EditListCtrl',
    link: function(scope, element, attrs) {

      var parent = element.find('.panel-heading')[0];
      var child = element.find('.panel-collapse')[0];

      scope.listOpen = lpEditorView.listState(scope.type);
      if (scope.listOpen) {
        jQuery(child).addClass('in');
      }

      jQuery(parent).bind('click', function() {
        jQuery(child).collapse(!!scope.listOpen ? 'hide' : 'show');
        scope.listOpen = !scope.listOpen;
        lpEditorView.toggleList(scope.type, scope.listOpen);
      });
    }
  }
}]);

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


angular.module('lampost_editor').directive('lmSkillList', [function () {
  return {
    restrict: 'A',
    scope: {},
    templateUrl: 'editor/view/skill_list.html',
    controller: 'SkillListController',
    link: function (scope, element, attrs) {
      element.scope().$watch(attrs.lmSkillList, function () {
        angular.extend(scope, element.scope().$eval(attrs.lmSkillList));
      })
    }
  }
}]);


angular.module('lampost_editor').controller('SkillListController', ['$q', '$scope', 'lmEditor', 'lpEvent',
  function ($q, $scope, lmEditor, lpEvent) {


    $scope.$on('updateModel', updateModel);

    lmEditor.cache('skill').then(function (skills) {
      $scope.allSkills = skills;
      ;
      $scope.ready = true;
      updateModel();
    });

    function updateModel() {
      if ($scope.$parent.model) {
        $scope.skillMap = $scope.$parent.model[$scope.attrWatch];
        updateUnused();
      }
    }

    function updateUnused() {
      $scope.unusedValues = [];
      angular.forEach($scope.allSkills, function (skill) {
        if (!$scope.skillMap.hasOwnProperty(skill.dbo_id)) {
          if ($scope.unusedValues.length === 0) {
            $scope.newId = skill.dbo_id;
          }
          $scope.unusedValues.push(skill);
        }
      });
    }

    $scope.deleteRow = function (rowId) {
      delete $scope.skillMap[rowId];
      updateUnused();
    };

    $scope.addRow = function () {
      $scope.skillMap[$scope.newId] = {skill_level: 1};
      updateUnused();
    };

  }]);

angular.module('lampost_editor').directive('lmOutsideEdit', [function () {
  return {
    restrict: 'E',
    replace: true,
    templateUrl: 'editor/view/outside_edit.html'
  }
}]);

angular.module('lampost_editor').directive('lpDataError', [function () {
  return {
    restrict: 'E',
    templateUrl: 'editor/view/data_error.html'
  }
}]);

angular.module('lampost_editor').directive('lmFormSubmit', [function () {
  return {
    restrict: 'A',
    link: function (scope, element, attrs) {
      element.bind('keypress', function (event) {
        if (event.keyCode == 13) {
          event.preventDefault();
          this.form.submit();
          return false;
        }
        return true;
      })
    }
  }
}]);

angular.module('lampost_editor').directive('lmObjectSelector', [function () {
  return {
    restrict: 'AE',
    templateUrl: 'editor/view/object_selector.html',
    controller: 'objSelectorController',
    link: function (scope, element, attrs) {
      scope.objType = attrs.lmObjectSelector;
    }
  }
}]);

angular.module('lampost_editor').controller('objSelectorController', ['$scope', 'lmEditor', 'lpEvent',
  function ($scope, lmEditor, lpEvent) {

    var listKey;
    var noObj = {dbo_id: "N/A"};

    $scope.$on('$destroy', function () {
      lmEditor.deref(listKey)
    });

    lpEvent.register('activateArea', function (newArea, oldArea) {
      if (newArea) {
        $scope.selectArea(newArea);
      } else if (oldArea == $scope.selectedArea) {
        $scope.selectArea(areaList[0]);
      }
    });

    $scope.selectedClass = function (area) {
      return $scope.selectedArea == area ? 'alert-info' : '';
    };

    lmEditor.cache('area').then(function (areas) {
      $scope.selectAreaList = areas;
      if (areas.indexOf($scope.startArea) > -1) {
        $scope.selectedArea = $scope.startArea;
      } else {
        $scope.selectedArea = areas[0];
      }
      $scope.selectArea();
    });

    $scope.selectArea = function (selectedArea) {
      $scope.selectedArea = selectedArea || $scope.selectedArea;
      $scope.selectedAreaId = $scope.selectedArea.dbo_id;
      if ($scope.areaChange) {
        $scope.areaChange($scope.selectedArea);
      }
      listKey = $scope.objType + ':' + $scope.selectedArea.dbo_id;
      lmEditor.cache(listKey).then(function (objects) {
        if ($scope.listChange) {
          $scope.listChange(objects);
        }
        $scope.areaObjList = objects;
        if (objects.length > 0) {
          $scope.selObjList = objects;
          $scope.hasAreaObj = true;
        } else {
          $scope.selObjList = [noObj];
          $scope.hasAreaObj = false;
        }
        $scope.selectedAreaObj = $scope.areaObjList[0];
      });
    };

  }]);

