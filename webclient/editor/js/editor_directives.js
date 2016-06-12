angular.module('lampost_editor').directive('lpEditList', ['lpEvent', 'lpEditorLayout',  function(lpEvent, lpEditorLayout) {

  return {
    scope: {},
    controller: 'EditListCtrl',
    templateUrl: 'editor/view/edit_list.html',
    link: function(scope, element, attrs, controller) {

      var parent = element.find('.panel-heading')[0];
      var child = element.find('.panel-collapse')[0];

      controller.initType(element.scope().$eval(attrs.lpEditList));

      var listOpen = lpEditorLayout.listState(scope.type);

      function update() {
        scope.toggleClass = 'fa fa-lg fa-caret-' + (listOpen ? 'up' : 'down');
      }

      if (listOpen) {
        jQuery(child).addClass('in');
      }
      update();

      jQuery(parent).bind('click', function() {
        listOpen = !listOpen;
        jQuery(child).collapse(listOpen ? 'show' : 'hide');
        lpEditorLayout.toggleList(scope.type, listOpen);
        scope.$apply(update);
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

angular.module('lampost_editor').directive('lpEditPanel', ['lpEditorLayout', function(lpEditorLayout) {
  return {
    link: function(scope, element, attrs) {
      var parent = element.find('.panel-heading')[0];
      var child = element.find('.panel-collapse')[0];
      var panelId = attrs.lpEditPanel;
      var panelOpen = lpEditorLayout.listState(panelId);

      function update() {
        scope.togglePanel = 'fa fa-lg fa-caret-' + (panelOpen ? 'up' : 'down');
      }

      if (panelOpen) {
        jQuery(child).addClass('in');
      }
      update();

      jQuery(parent).bind('click', function() {
        panelOpen = !panelOpen;
        jQuery(child).collapse(panelOpen ? 'show' : 'hide');
        lpEditorLayout.toggleList(panelId, panelOpen);
        scope.$apply(update);
      });
    }
  }
}]);


angular.module('lampost_editor').controller('ValueSetCtrl', ['$scope', 'lpEvent',
 function ($scope, lpEvent) {
  $scope.remove = function (row, rowIx) {
    $scope.valueSet.remove(row, rowIx);
    lpEvent.dispatch('childUpdate');
  };

  $scope.change = function(row, rowIx) {
     $scope.valueSet.onChange(row, rowIx);
     lpEvent.dispatch('childUpdate');
  };

  $scope.insert = function () {
    $scope.valueSet.insert();
    lpEvent.dispatch('childUpdate');
  };

  this.startEdit = function(model) {
      $scope.can_write = model.can_write;
      $scope.valueSet.setSource(model);
      $scope.groupClass = $scope.valueSet.size ? 'input-group-' + $scope.valueSet.size : '';
  };

  lpEvent.register('editReady', this.startEdit, $scope);

}]);

angular.module('lampost_editor').directive('lpValueSet', [function () {
  return {
    restrict: 'A',
    scope: {},
    templateUrl: 'editor/view/value_set.html',
    controller: 'ValueSetCtrl',
    link: function (scope, element, attrs, controller) {
      scope.valueSet = scope.$parent.$eval(attrs.lpValueSet);
      controller.startEdit(scope.$parent.model);
      scope.$parent.$emit('lpDirectiveLoaded');
    }
  }
}]);


angular.module('lampost_editor').directive('lpOptionsList', [function () {
  return {
    restrict: 'A',
    scope: {},
    templateUrl: 'editor/view/simple_list.html',
    controller: 'ValueSetCtrl',
    link: function (scope, element, attrs, controller) {
      scope.valueSet = scope.$parent.$eval(attrs.lpOptionsList);
      controller.startEdit(scope.$parent.model);
      scope.$parent.$emit('lpDirectiveLoaded');
    }
  }
}]);


angular.module('lampost_editor').directive('lpDisabled', ['$timeout', function($timeout) {
  return {
    restrict: 'A',
    link: function(scope, element, attrs) {

      var disabled = false;
      var disablePending = false;
      function disableIt() {
        if (disablePending) {
          return;
        }
        disablePending = true;
        $timeout(function () {
          var elements = element.find(':input').not('.never-disable').not('[ng-disabled]');
          elements.prop('disabled', disabled);
          // This keeps the 'EnableUI' method of the dialog service from re-enabling these elements
          if (disabled) {
            elements.attr('_lp_disabled', 'true')
          } else {
            elements.removeAttr('_lp_disabled');
          }
          disablePending = false;
        });
      }
      scope.$watch(attrs.lpDisabled, function(value) {
        disabled = value;
        disableIt();
      });

      scope.$on('$includeContentLoaded', disableIt);
      scope.$on('lpDirectiveLoaded', disableIt);
    }
  }
}]);

angular.module('lampost_editor').directive('lpOutsideEdit', [function () {
  return {
    restrict: 'E',
    replace: true,
    templateUrl: 'editor/view/outside_edit.html'
  }
}]);

angular.module('lampost_editor').directive('lpDataError', [function () {
  return {
    restrict: 'E',
    scope: {},
    templateUrl: 'editor/view/data_error.html',
    link: function(scope, element, attrs) {
      scope.errors = element.scope().errors;
      scope.type = attrs.type || 'dataError';
    }
  }
}]);

angular.module('lampost_editor').controller('OwnerIdCtrl', ['$scope', 'lpCache', 'lpEditor',
  function($scope, lpCache, lpEditor) {

    var origOwner = $scope.model.owner_id;

    $scope.checkOwner = function() {
      var newImm = lpCache.cachedValue('immortal:' + $scope.model.owner_id);
      if (newImm.imm_level > lpEditor.immLevel) {
        $scope.errors.owner = "Owner is higher level than you.";
        $scope.model.owner_id = origOwner;
      } else {
        origOwner = $scope.model.owner_id;
        $scope.model.read_access = 0;
        $scope.model.write_access = 0;
        $scope.errors.owner = null;
      }
    }
}]);

angular.module('lampost_editor').directive('lpOwnerId', [function() {
  return {
    restrict: 'AE',
    controller: 'OwnerIdCtrl',
    templateUrl: 'editor/fragments/owner_id.html',
    link: function(scope) {
      scope.$parent.$emit('lpDirectiveLoaded');
    }
  }
}]);


angular.module('lampost_editor').controller('ChildSelectorCtrl', ['$scope', '$attrs', '$filter', 'lpEvent', 'lpCache', 'lpEditor',
  function($scope, $attrs, $filter, lpEvent, lpCache, lpEditor) {

  var childSelect, selectId, context, parentKey, childKey, cacheObj, invalid;

  invalid = {dbo_id: "--N/A--", name: "--N/A--", title: "--N/A--", invalid: true};
  selectId = $attrs.lpChildSelect;
  childSelect = $scope.$eval(selectId);
  context = lpEditor.getContext(childSelect.type);
  parentKey = context.parentType;

  $scope.$on('$destroy', function () {
    lpCache.deref(childKey);
    lpCache.deref(parentKey);
  });

  function parentList() {
    lpCache.deref(parentKey);
    lpCache.cache(parentKey).then(function(parents) {
      $scope.parentList = $filter(childSelect.parentFilter[0]).apply(null, [parents].concat(childSelect.parentFilter.slice(1)));
      if ($scope.parentList.length) {
        $scope.parent = $scope.parentList[0];
        if (typeof childSelect.value === 'string') {
          cacheObj = lpCache.cachedValue(parentKey + ':' + childSelect.value.split(':')[0]);
          if (cacheObj && $scope.parentList.indexOf(cacheObj) > -1) {
            $scope.parent = cacheObj;
          } else {
            $scope.errors[selectId] = "Original value " + childSelect.value + " is no long valid.";
          }
        }
      } else {
        $scope.errors[selectId] = "No valid values.";
        $scope.parentList = [invalid];
        $scope.parent = invalid;
      }
      $scope.selectParent();
    });
  }

  function childList() {
    lpCache.deref(childKey);
    childKey = childSelect.type + ':' + $scope.parent.dbo_id;
    lpCache.cache(childKey).then(function(children) {
      $scope.childList = $filter(childSelect.childFilter[0]).apply(null, [children].concat(childSelect.childFilter.slice(1)));
      if ($scope.childList.length) {
        if (typeof childSelect.value === 'string' && childSelect.value.split(':')[0] === $scope.parent.dbo_id) {
          cacheObj = childSelect.value && lpCache.cachedValue(childSelect.type + ':' + childSelect.value);
          if (cacheObj && $scope.childList.indexOf(cacheObj) > -1) {
            $scope.child = cacheObj.dbo_id;
          } else {
            $scope.errors[selectId] = "Original value " + childSelect.value + " not found.";
          }
        } else {
          delete $scope.child;
        }
      } else {
        $scope.childList = [invalid];
        $scope.child = invalid;
        $scope.errors[selectId] = "No child found for " + $scope.parent.dbo_id + ".";
      }
    })
  }

  $scope.selectParent = function() {
    if ($scope.parent.invalid) {
      $scope.childList = [invalid];
      $scope.child = invalid;
    } else {
      childSelect.parentSelect();
      childList();
    }
  };

  $scope.selectChild = function() {
    if ($scope.child && !$scope.child.invalid) {
      childSelect.childSelect();
      childSelect.setValue($scope.child);
      lpEvent.dispatch('childUpdate');
    }
  };

  this.startEdit = function() {
    $scope.can_write = $scope.model.can_write;
    delete $scope.parent;
    delete $scope.child;
    childSelect.setSource($scope.model);
    parentList();
  };

  this.startAddEdit = function(addObj) {
    $scope.can_write = $scope.model.can_write;
    delete $scope.parent;
    delete $scope.child;
    childSelect.setSource(addObj);
    parentList();
  };

  lpEvent.register("modelDeleted", parentList, $scope);
  lpEvent.register("modelUpdated", parentList, $scope);
  lpEvent.register("modelInserted", parentList, $scope);
  lpEvent.register('editReady', this.startEdit, $scope);
  if ($scope.addObj) {
    this.startAddEdit($scope.addObj);
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
        if (parentFilter) {
          var f = parentFilter.split(":");
          $scope.sourceList = $filter(f[0])(parents, f[1]);
        } else {
          $scope.sourceList = parents;
        }
        $scope.vars.parent = lpCache.cachedValue(parentKey + ':' + parentId);
        loadChildren();
      });
    }

    function loadChildren() {
      lpCache.deref(listKey);
      listKey = type + ':' + parentId;
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
