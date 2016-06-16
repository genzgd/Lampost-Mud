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
    $scope.addPanel = null;

    $scope.syncSlot = function() {
        $scope.model.equip_slot = $scope.locals.equipSlot == '[none]' ? null : $scope.locals.equipSlot;
    };

    lpEvent.register('editReady', function() {
      $scope.locals.equipSlot = lpEditor.original.equip_slot ? lpEditor.original.equip_slot : '[none]';
      $scope.closeAdd();
    });

    $scope.addScript = function(event) {
      if (event) {
        event.stopImmediatePropagation();
        event.preventDefault();
      }
      $scope.addPanel = 'editor/panels/new_script.html';
    };

    $scope.modifyScript = function(scriptRef) {
      lpEditor.addObj = scriptRef;
      $scope.addPanel = 'editor/panels/modify_script.html';
    };

    $scope.closeAdd = function() {
      $scope.addPanel = null;
    }


  }]);
