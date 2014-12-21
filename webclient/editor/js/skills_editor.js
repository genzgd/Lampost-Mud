angular.module('lampost_editor').service('lpSkillService', ['$q', 'lpEvent', 'lpRemote', 'lpEvent', 'lpEditor',
 function($q, lpEvent, lpRemote, lpEvent, lpEditor) {

    var skillMap;
    var self = this;
    var promise;;

    this.loadMap = function() {
        if (skillMap) {
            return $q.when(skillMap);
        }
        if (!promise) {
            promise = lpRemote.request('editor/skill_map').then(function(map) {
                self.skillMap = map;
                return $q.when(map);
            })
        }
        return promise;
    }

    lpEvent.register('modelCreate', function(model) {
        if (lpEditor.constants.skill_types.indexOf(model.dbo_key_type) > -1) {
            skillMap[model.dbo_key] = model;
        }
    });

    lpEvent.register('modelUpdate', function(model) {
        if (skillMap.hasOwnProperty(model.dbo_key)) {
            skillMap[model.dbo_key] = model;
        }
    });

    lpEvent.register('modelDelete', function(model) {
        delete skillMap[model.dbo_key];
    });

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


angular.module('lampost_editor').controller('RaceEditorCtrl', ['$scope', 'lpEditor', 'lpSkillService',
  function ($scope, lpEditor, lpSkillService) {

    var attr_map = lpEditor.constants.attr_map;

    $scope.defaultAttrsList = {effectDesc: "Starting attributes for this race", effectName: "Starting Attributes",
      calcWatch: 'base_attrs', calcDefs: attr_map, effectLabel: function(id) {
        return attr_map[id].name;
      }, fixed: true};

    $scope.defaultSkills = {effectDesc: "Default skills and levels assigned to this race", effectName: "Default Skills",
          calcWatch: "default_skills", calcDefs: lpSkillService.skillMap};

  }]);
