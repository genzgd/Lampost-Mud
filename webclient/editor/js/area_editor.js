angular.module('lampost_editor').controller('MobileEditorCtrl', ['$scope', 'lpEditorTypes', 'lpSkillService',
  function ($scope, lpEditorTypes, lpSkillService) {

    var skillSet = new lpEditorTypes.ValueObjList('default_skills', "Default Skills [Level]", 'skill_template', 'skill_level');
    skillSet.options = lpSkillService.allSkills();
    skillSet.optionKey = 'dbo_key';
    $scope.skillSet = skillSet;

  }]);


angular.module('lampost_editor').controller('ArticleEditorCtrl', ['$scope', 'lpEvent', 'lpEditor',
  function ($scope, lpEvent, lpEditor) {

    $scope.locals = {};
    $scope.equip_slots = angular.copy($scope.constants.equip_slots);
    $scope.equip_slots.unshift('[none]');

    $scope.syncSlot = function() {
        $scope.model.equip_slot = $scope.locals.equipSlot == '[none]' ? null : $scope.locals.equipSlot;
    };

    lpEvent.register('editReady', function() {
      $scope.locals.equipSlot = lpEditor.original.equip_slot ? lpEditor.original.equip_slot : '[none]';
    });

  }]);
