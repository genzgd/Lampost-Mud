angular.module('lampost_editor').directive('lpEditList', ['lpEvent', 'lpEditorView',  function(lpEvent, lpEditorView) {

  return {
    scope: {},
    controller: 'EditListCtrl',
    templateUrl: 'editor/view/edit_list.html',
    link: function(scope, element, attrs, controller) {

      var parent = element.find('.panel-heading')[0];
      var child = element.find('.panel-collapse')[0];

      controller.initType(element.scope().$eval(attrs.lpEditList));

      function update() {

        scope.toggleClass = 'fa fa-lg fa-caret-' + (scope.listOpen ? 'up' : 'down');
      }

      scope.listOpen = lpEditorView.listState(scope.type);
      if (scope.listOpen) {
        jQuery(child).addClass('in');
      }
      update();

      jQuery(parent).bind('click', function() {
        scope.listOpen = !scope.listOpen;
        jQuery(child).collapse(scope.listOpen ? 'show' : 'hide');
        lpEditorView.toggleList(scope.type, scope.listOpen);
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

