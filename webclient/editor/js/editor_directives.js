angular.module('lampost_editor').directive('lpEditList', ['lpEvent', 'lpEditorView',  function(lpEvent, lpEditorView) {

  return {
    scope: {},
    controller: 'EditListCtrl',
    templateUrl: 'editor/view/edit_list.html',
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

      scope.newEditor = function (editorId, event) {
        if (event) {
          event.preventDefault();
          event.stopPropagation();
        }
        lpEvent.dispatch('newEdit', editorId);
      }
    }
  }
}]);

angular.module('lampost_editor').controller('EffectListCtrl', ['$scope', 'lpEvent',
 function ($scope, lpEvent) {

  $scope.vars = {};
  $scope.effectLabel = function(calcId) {
    return calcId;
  }

  var updateList;

  function updateUnused() {
    $scope.unusedValues = [];
    angular.forEach($scope.calcDefs, function (value, key) {
      if (!$scope.calcValues.hasOwnProperty(key)) {
        if ($scope.unusedValues.length === 0) {
          $scope.vars.newId = key;
        }
        $scope.unusedValues.push(key);
      }
    });
  }

  $scope.deleteRow = function (rowId) {
    delete $scope.calcValues[rowId];
    lpEvent.dispatch('childUpdate');
    updateList();
  };

  $scope.childUpdate = function() {
     lpEvent.dispatch('childUpdate');
  };

  $scope.addRow = function () {
    $scope.calcValues[$scope.vars.newId] = 1;
    lpEvent.dispatch('childUpdate');
    updateList();
  };

  this.startEdit = function() {
    $scope.calcValues = $scope.$parent.model[$scope.calcWatch];
    $scope.can_write = $scope.$parent.model.can_write;
    updateList = $scope.fixed ? angular.noop : updateUnused;
    updateList();
  };

  lpEvent.register('editStarting', this.startEdit, $scope);

}]);

angular.module('lampost_editor').directive('lpEffectList', [function () {
  return {
    restrict: 'A',
    scope: {},
    templateUrl: 'editor/view/effect_list.html',
    controller: 'EffectListCtrl',
    link: function (scope, element, attrs, controller) {
      angular.extend(scope, element.scope().$eval(attrs.lpEffectList));
      controller.startEdit();
    }
  }
}]);

angular.module('lampost_editor').controller('OptionsListCtrl', ['$scope', 'lpEvent', function ($scope, lpEvent) {

  $scope.vars = {};

  function updateUnused() {
    $scope.unusedValues = [];
    angular.forEach($scope.selectDefs, function (value, key) {
      if ($scope.selectValues.indexOf(key) === -1) {
        if ($scope.unusedValues.length === 0) {
          $scope.vars.newSelection = key;
        }
        $scope.unusedValues.push(key);
      }
    });
  }

  $scope.deleteRow = function (selection) {
    var ix = $scope.selectValues.indexOf(selection);
    $scope.selectValues.splice(ix, 1);
    lpEvent.dispatch('childUpdate');
    updateUnused();
  };

  $scope.addRow = function () {
    $scope.selectValues.push($scope.vars.newSelection);
    lpEvent.dispatch('childUpdate');
    updateUnused();
  };

  this.startEdit = function () {
     $scope.selectValues = $scope.$parent.model[$scope.optionsWatch];
     $scope.can_write = $scope.$parent.model.can_write;
     updateUnused();
  }

  lpEvent.register('editStarting', this.startEdit, $scope);

}]);

angular.module('lampost_editor').directive('lpOptionsList', [function () {
  return {
    restrict: 'A',
    scope: {},
    templateUrl: 'editor/view/simple_list.html',
    controller: 'OptionsListCtrl',
    link: function (scope, element, attrs, controller) {
      angular.extend(scope, element.scope().$eval(attrs.lpOptionsList));
      controller.startEdit();
    }
  }
}]);

angular.module('lampost_editor').directive('lpSkillList', [function () {
  return {
    restrict: 'A',
    scope: {},
    templateUrl: 'editor/view/skill_list.html',
    controller: 'SkillListCtrl',
    link: function (scope, element, attrs) {
      angular.extend(scope, element.scope().$eval(attrs.lmSkillList));
    }
  }
}]);


angular.module('lampost_editor').controller('SkillListCtrl', ['$q', '$scope', 'lmEditor', 'lpEvent',
  function ($q, $scope, lmEditor, lpEvent) {


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
    var parentFilter;
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
      parentFilter = $scope[$attrs.lpParentFilter] || $scope.parentFilter;
      listChange = $scope[$attrs.lpListChange] || $scope.listChange || angular.noop;
      lpCache.deref(parentKey);
      parentKey = context.parentType;
      lpCache.cache(parentKey).then(function (parents) {
        $scope.sourceList = parentFilter ? $filter(parentFilter)(parents) : parents;
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

