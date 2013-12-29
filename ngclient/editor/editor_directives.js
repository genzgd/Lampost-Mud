angular.module('lampost_editor').service('EditorHelper', ['$q', 'lmBus', 'lmRemote', 'lmEditor', 'lmDialog', 'lmUtil',
  function ($q, lmBus, lmRemote, lmEditor, lmDialog, lmUtil) {

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


angular.module('lampost_editor').controller('SkillListController', ['$q', '$scope', 'lmEditor',
  function ($q, $scope, lmEditor) {

    $scope.allSkills = [];
    $scope.ready = false;

    $scope.$on('updateModel', updateModel);

    $q.all([
        lmEditor.cache('attack').then(function (attacks) {
          $scope.allSkills = $scope.allSkills.concat(attacks);
        }),
        lmEditor.cache('defense').then(function (defenses) {
          $scope.allSkills = $scope.allSkills.concat(defenses);
        })]).then(function () {
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
      $scope.skillMap[$scope.newId] =  {skill_level: 1};
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

angular.module('lampost_editor').directive('lmRoomSelector', [function () {
  return {
    restrict: 'AE',
    controller: 'roomSelectorController'
  }
}]);


angular.module('lampost_editor').controller('roomSelectorController', ['$scope', 'lmEditor',
  function($scope, lmEditor) {

    var listKey;
    lmEditor.cache('area').then(function (areas) {
      $scope.selectAreaList = areas;
      if (!$scope.selectedArea && $scope.selectedAreaId) {
        $scope.selectedArea = lmCacheValue('area', $scope.selectedAreaId);
      } else {
        $scope.selectedArea = areas[0];
      }
      $scope.selectArea($scope.selectedArea);
    });

    $scope.$on('$destroy', function() {
      lmEditor.deref(listKey)
    });

    $scope.selectedClass = function(area) {
      return $scope.selectedArea == area ? 'alert-info': '';
    };

    $scope.selectArea = function (selectedArea) {
      if (selectedArea) {
        $scope.selectedArea = selectedArea;
      }
      lmEditor.deref(listKey);
      listKey = 'room:' + $scope.selectedArea.dbo_id;
      lmEditor.cache(listKey).then(function (rooms) {
        $scope.selectRoomList = rooms;
        $scope.selectedRoom = rooms[0];
      });
    };


}]);
