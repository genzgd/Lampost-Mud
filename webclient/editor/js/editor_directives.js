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

angular.module('lampost_editor').controller('ChildSelectCtrl',
  ['$scope', '$attrs', '$filter', 'lpCache', 'lpEvent', 'lpEditor',
  function ($scope, $attrs, $filter, lpCache, lpEvent, lpEditor) {

    var parentKey;
    var listKey;
    var listChange;
    var parentId;
    var type = $attrs.lpChildType;
    var context = lpEditor.getContext(type);

    $scope.$on('$destroy', function () {
      lpCache.deref(listKey);
      lpCache.deref(parentKey);
    });

    function initialize() {
      $scope.vars = {};
      parentId = $scope[$attrs.lpListParent] || context.parent.dbo_id;
      listChange = $scope[$attrs.lpListChange] || $scope.listChange || angular.noop;
      lpCache.deref(parentKey);
      parentKey = context.parentType;
      lpCache.cache(parentKey).then(function (parents) {
        $scope.sourceList = parents;
        $scope.vars.parent = lpCache.cacheValue(parentKey, parentId);
        loadChildren();
      });
    }

    function loadChildren() {
      lpCache.deref(listKey);
      listKey = type + ':' + parentId
      lpCache.cache(listKey).then(function (children) {
        $scope.childList = children;
        listChange(children);
      });
    }

    $scope.selectParent = function () {
      if (!$scope.vars.parent) {
        return;
      }
      parentId = $scope.vars.parent.dbo_id;
      loadChildren();
    };

    lpEvent.register("modelDeleted", initialize, $scope);
    lpEvent.register("modelUpdated", initialize, $scope);
    lpEvent.register("modelInserted", initialize, $scope);

    initialize();

  }]);

