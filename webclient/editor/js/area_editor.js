angular.module('lampost_editor').controller('MobileEditorCtrl', [function () {

    $scope.defaultSkills = {effectDesc: "Default skills and levels assigned to this mobile", effectName: "Default Skills",
      attrWatch: "default_skills"};

  }]);


angular.module('lampost_editor').controller('ArticleEditorCtrl', ['$scope', 'lpEditor',
  function ($scope, lpEditor) {

    $scope.locals = {};
    $scope.equip_slots = angular.copy($scope.constants.equip_slots);
    $scope.equip_slots.unshift('[none]');

    $scope.syncSlot = function() {
        $scope.model.equip_slot = $scope.locals.equipSlot == '[none]' ? null : $scope.locals.equipSlot;
    };

    $scope.locals.equipSlot = lpEditor.original.equip_slot ? lpEditor.original.equip_slot : '[none]';

  }]);
