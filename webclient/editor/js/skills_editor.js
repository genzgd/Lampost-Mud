angular.module('lampost_editor').service('lpSkillService', ['$q', 'lpCache', 'lpEditor',
  function($q, lpCache, lpEditor) {

    var skillMap;
    var self = this;
    var promise;
    var skillLists = [];

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

angular.module('lampost_editor').controller('AttackEditorCtrl', ['$scope',
  function ($scope) {

    $scope.damageList = {effectDesc: 'Calculation of Damage based on attributes and roll', effectName: 'Damage Calculation',
      calcWatch: 'damage_calc', calcDefs: $scope.constants.calc_map};

    $scope.accuracyList = {effectDesc: 'Calculation of Accuracy based on attributes and roll', effectName: 'Accuracy Calculation',
      calcWatch: 'accuracy_calc', calcDefs: $scope.constants.calc_map};

    $scope.costList = {effectDesc: 'Calculation of Pool costs based on attributes and skill level',
      effectName: 'Cost calculation', calcWatch: 'costs', calcDefs: $scope.constants.resource_pools};

  }]);


angular.module('lampost_editor').controller('DefenseEditorCtrl', ['$scope', function ($scope) {

    $scope.avoidList = {effectDesc: 'Chance to avoid attack based on attributes and roll', effectName: 'Avoid Calculation',
      calcWatch: 'avoid_calc', calcDefs: $scope.constants.calc_map};

    $scope.absorbList = {effectDesc: 'Absorb calculation based on attributes and roll', effectName: 'Absorb Calculation',
      calcWatch: 'absorb_calc', calcDefs: $scope.constants.calc_map};

    $scope.costList = {effectDesc: 'Calculation of Pool costs based on attributes and skill level',
      effectName: 'Cost calculation', calcWatch: 'costs', calcDefs: $scope.constants.resource_pools};

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

    var attr_map = lpEditor.constants.attr_map;

    var attrSet = new lpEditorTypes.ValueMap('base_attrs', 'Starting Attributes');
    attrSet.rowLabel = function(row) {
      return attr_map[row.key].name;
    };

    $scope.attrSet = attrSet;

    var skillSet = new lpEditorTypes.ValueObjList('default_skills', "Default Skills", 'skill_template', 'skill_level');
    skillSet.options = lpSkillService.allSkills();
    skillSet.optionKey = 'dbo_key';
    $scope.skillSet = skillSet;

  }]);
