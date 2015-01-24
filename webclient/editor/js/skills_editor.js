angular.module('lampost_editor').service('lpSkillService', [ 'lpCache', 'lpEditor',
  function(lpCache, lpEditor) {

    this.allSkills = function() {
      var skillLists = [];
      angular.forEach(lpEditor.constants.skill_types, function(skillType) {
        skillLists.push(lpCache.cachedList(skillType));
      });
      return [].concat.apply([], skillLists);
    };

  }]);

angular.module('lampost_editor').controller('AttackEditorCtrl', ['$scope', 'lpEditor', 'lpEditorTypes',
  function ($scope, lpEditor, lpEditorTypes) {

    var damageList = new lpEditorTypes.ValueMap('damage_calc', 'Damage Calculation');
    damageList.desc = 'Calculation of Damage based on attributes and roll';
    damageList.options = lpEditor.constants.skill_calculation;
    damageList.size = 'sm';
    $scope.damageList = damageList;

    var accuracyList = new lpEditorTypes.ValueMap('accuracy_calc', 'Accuracy Calculation');
    accuracyList.desc = 'Calculation of Accuracy based on attributes and roll';
    accuracyList.options = lpEditor.constants.skill_calculation;
    accuracyList.size = 'sm';
    $scope.accuracyList = accuracyList;

    var costList = new lpEditorTypes.ValueMap('costs', 'Skill Costs');
    costList.options = lpEditor.constants.resource_pools;
    costList.size = 'sm';
    $scope.costList = costList;

  }]);


angular.module('lampost_editor').controller('DefenseEditorCtrl', ['$scope', 'lpEditor', 'lpEditorTypes',
  function ($scope, lpEditor, lpEditorTypes) {

    var absorbList = new lpEditorTypes.ValueMap('absorb_calc', 'Absorb Calculation');
    absorbList.desc = 'Calculation of absorb amount based on attributes and roll';
    absorbList.options = lpEditor.constants.skill_calculation;
    absorbList.size = 'sm';
    $scope.absorbList = absorbList;

    var avoidList = new lpEditorTypes.ValueMap('avoid_calc', 'Avoid Calculation');
    avoidList.desc = 'Calculation of avoid chance based on attributes and roll';
    avoidList.options = lpEditor.constants.skill_calculation;
    avoidList.size = 'sm';
    $scope.avoidList = avoidList;

    var costList = new lpEditorTypes.ValueMap('costs', 'Skill Costs');
    costList.options = lpEditor.constants.resource_pools;
    costList.size = 'sm';
    $scope.costList = costList;

    $scope.damageTypes = new lpEditorTypes.OptionsList('damage_type', 'Damage Types');
    $scope.damageTypes.desc = 'List of damage types this defense is effective against';
    $scope.damageTypes.setOptions(lpEditor.constants.defense_damage_types);

    $scope.deliveryTypes = new lpEditorTypes.OptionsList('delivery', 'Delivery Methods');
    $scope.deliveryTypes.desc = 'List of delivery methods this defense is effective against';
    $scope.deliveryTypes.setOptions(lpEditor.constants.damage_delivery);

    $scope.onAutoStart = function () {
      if ($scope.model.auto_start) {
        $scope.model.verb = undefined;
      }
    };

  }]);


angular.module('lampost_editor').controller('RaceEditorCtrl', ['$scope', 'lpEditor', 'lpEditorTypes', 'lpSkillService',
  function ($scope, lpEditor, lpEditorTypes, lpSkillService) {

    var attr_map = {};

    angular.forEach(lpEditor.constants.attributes, function(attr) {
      attr_map[attr.dbo_id] = attr;
    });

    var attrSet = new lpEditorTypes.ValueMap('base_attrs', 'Starting Attributes');
    attrSet.rowLabel = function(row) {
      return attr_map[row.key].name;
    };

    $scope.attrSet = attrSet;

    var skillSet = new lpEditorTypes.ValueObjList('default_skills', "Default Skills [Level]", 'skill_template', 'skill_level');
    skillSet.options = lpSkillService.allSkills();
    skillSet.optionKey = 'dbo_key';
    $scope.skillSet = skillSet;

    $scope.startRoomSelect = new lpEditorTypes.ChildSelect('start_room', 'room');

  }]);
