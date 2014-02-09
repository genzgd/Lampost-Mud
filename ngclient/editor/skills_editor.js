angular.module('lampost_editor').controller('AttackEditorCtrl', ['$q', '$scope', '$filter', 'lmEditor', 'lmDialog',
  function ($q, $scope, $filter, lmEditor, lmDialog) {

    this.subClassId = 'attack';

    $scope.$watch('modelList', function(models) {
      $scope.attackList = $filter('filter')(models, {sub_class_id: 'attack'});
    }, true);

    $scope.damageList = {effectDesc: 'Calculation of Damage based on attributes and roll', effectName: 'Damage Calculation',
      calcWatch: 'damage_calc', calcDefs: $scope.constants.calc_map};

    $scope.accuracyList = {effectDesc: 'Calculation of Accuracy based on attributes and roll', effectName: 'Accuracy Calculation',
      calcWatch: 'accuracy_calc', calcDefs: $scope.constants.calc_map};

    $scope.costList = {effectDesc: 'Calculation of Pool costs based on attributes and skill level',
      effectName: 'Cost calculation', calcWatch: 'costs', calcDefs: $scope.constants.resource_pools};

    lmEditor.prepare(this, $scope).prepareList('skill');

    this.preCreate = function (attack) {
      attack.verb = attack.dbo_id;
    };

    this.preUpdate = function (attack) {
      if (attack.damage_type == 'weapon' && attack.weapon_type == 'unused') {
        lmDialog.showOk("Invalid Weapon/Damage Types",
          "Damage type of weapon with 'Unused' weapon is invalid.")
        return $q.reject();
      }
      return $q.when();
    }

  }]);


angular.module('lampost_editor').controller('DefenseEditorCtrl', ['$q', '$filter', 'lmDialog', '$scope', 'lmEditor',
  function ($q, $filter, lmDialog, $scope, lmEditor) {

    this.subClassId = 'defense';

    $scope.$watch('modelList', function(models) {
      $scope.defenseList = $filter('filter')(models, {sub_class_id: 'defense'});
    }, true);

    $scope.avoidList = {effectDesc: 'Chance to avoid attack based on attributes and roll', effectName: 'Avoid Calculation',
      calcWatch: 'avoid_calc', calcDefs: $scope.constants.calc_map};

    $scope.absorbList = {effectDesc: 'Absorb calculation based on attributes and roll', effectName: 'Absorb Calculation',
      calcWatch: 'absorb_calc', calcDefs: $scope.constants.calc_map};

    $scope.costList = {effectDesc: 'Calculation of Pool costs based on attributes and skill level',
      effectName: 'Cost calculation', calcWatch: 'costs', calcDefs: $scope.constants.resource_pools};

    $scope.damageTypeList = {selectDesc: 'List of damage types this defense is effective against',
      selectName: 'Damage Types', selectWatch: 'damage_type', selectDefs: $scope.constants.defense_damage_types};

    $scope.deliveryTypeList = {selectDesc: 'List of delivery methods this defense is effective against',
      selectName: 'Delivery Methods', selectWatch: 'delivery', selectDefs: $scope.constants.damage_delivery};

    $scope.onAutoStart = function () {
      if ($scope.model.auto_start) {
        $scope.model.verb = undefined;
      }
    };

    this.preCreate = function (defense) {
      defense.verb = defense.dbo_id;
    };

    this.preUpdate = function (model) {
      if (!model.auto_start && !model.verb) {
        lmDialog.showOk("Start Method Required", "Either a command or 'autoStart' is required");
        return $q.reject();
      }
      return $q.when();
    };

    lmEditor.prepare(this, $scope).prepareList('skill');

  }]);


angular.module('lampost_editor').controller('RaceEditorCtrl', ['$scope', 'lmEditor',
  function ($scope, lmEditor) {

    $scope.defaultAttrsList = {listDesc: "Starting attributes for this race", listName: "Starting Attributes",
      attrWatch: 'base_attrs', attrDefs: $scope.constants.attr_map};

    $scope.defaultSkills = {effectDesc: "Default skills and levels assigned to this race", effectName: "Default Skills",
          attrWatch: "default_skills"};

    lmEditor.prepare(this, $scope).prepareList('race');

  }]);
