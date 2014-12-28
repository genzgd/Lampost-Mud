angular.module('lampost_editor').directive('lpEditList', ['lpEvent', 'lpEditorView',  function(lpEvent, lpEditorView) {

  return {
    scope: {},
    controller: 'EditListCtrl',
    templateUrl: 'editor/view/edit_list.html',
    link: function(scope, element, attrs, controller) {

      var parent = element.find('.panel-heading')[0];
      var child = element.find('.panel-collapse')[0];

      controller.initType(element.scope().$eval(attrs.lpEditList));

      var listOpen = lpEditorView.listState(scope.type);

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
        lpEditorView.toggleList(scope.type, listOpen);
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

angular.module('lampost_editor').directive('lpEditPanel', ['lpEditorView', function(lpEditorView) {
  return {
    link: function(scope, element, attrs) {
      var parent = element.find('.panel-heading')[0];
      var child = element.find('.panel-collapse')[0];
      var panelId = attrs.lpEditPanel;
      var panelOpen = lpEditorView.listState(panelId);

      function update() {
        scope.toggleClass = 'fa fa-lg fa-caret-' + (panelOpen ? 'up' : 'down');
      }

      if (panelOpen) {
        jQuery(child).addClass('in');
      }
      update();

      jQuery(parent).bind('click', function() {
        panelOpen = !panelOpen;
        jQuery(child).collapse(panelOpen ? 'show' : 'hide');
        lpEditorView.toggleList(panelId, panelOpen);
        scope.$apply(update);
      });
    }
  }
}])


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
      function disableIt() {
        $timeout(function () {
          var elements = element.find(':input').not('.never-disable').not('[ng-disabled]');
          elements.prop('disabled', disabled);
          // This keeps the 'EnableUI' method of the dialog service from re-enabling these elements
          if (disabled) {
            elements.attr('_lp_disabled', 'true')
          } else {
            elements.removeAttr('_lp_disabled');
          }
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
      var newImm = lpCache.cacheValue('immortal:' + $scope.model.owner_id);
      if (newImm.imm_level > lpEditor.immLevel) {
        $scope.errors.owner = "Owner is higher level than you.";
        $scope.model.owner_id = origOwner;
      } else {
        origOwner = $scope.model.owner_id;
        $scope.errors.owner = null;
      }
    }
}])

angular.module('lampost_editor').directive('lpOwnerId', [function() {
  return {
    restrict: 'AE',
    controller: 'OwnerIdCtrl',
    templateUrl: 'editor/fragments/owner_id.html',
    link: function(scope, element, attrs) {
      scope.$parent.$emit('lpDirectiveLoaded');
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
        $scope.vars.parent = lpCache.cacheValue(parentKey + ':' + parentId);
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