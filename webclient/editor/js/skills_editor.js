angular.module('lampost_editor').service('lpSkillService', ['$q', 'lpEvent', 'lpCache', 'lpEditor',
  function($q, lpEvent, lpCache, lpEditor) {

    var promise;
    var skillLists = [];

    lpEvent.register('cacheCleared', function() {
      promise = null;
      skillList = [];
    });

    this.preLoad = function() {
      var promises = [];
      var skillTypes = lpEditor.constants.skill_types;
      if (!promise) {
        for (var ix = 0; ix < skillTypes.length; ix++) {
          promises.push(lpCache.cache(skillTypes[ix]).then(function(skills) {
              skillLists.push(skills);
            }
          ));
        }
      }
      promise = $q.all(promises);
      return promise;
    };

    this.allSkills = function() {
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

    $scope.damageTypeList = {selectDesc: 'List of damage types this defense is effective against',
      selectName: 'Damage Types', optionsWatch: 'damage_type', selectDefs: $scope.constants.defense_damage_types};

    $scope.deliveryTypeList = {selectDesc: 'List of delivery methods this defense is effective against',
      selectName: 'Delivery Methods', optionsWatch: 'delivery', selectDefs: $scope.constants.damage_delivery};

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

  }]);
