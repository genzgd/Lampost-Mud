angular.module('lampost_editor').controller('AttackEditorCtrl', ['$scope', 'EditorHelper', function ($scope, EditorHelper) {

  this.modelList = {key: 'attack'};

  $scope.damageList = {effectDesc: 'Calculation of Damage based on attributes and roll', effectName: 'Damage Calculation',
    calcWatch: 'damage_calc', calcDefs: $scope.constants.calc_map};

  $scope.accuracyList = {effectDesc: 'Calculation of Accuracy based on attributes and roll', effectName: 'Accuracy Calculation',
    calcWatch: 'accuracy_calc', calcDefs: $scope.constants.calc_map};

  $scope.costList = {effectDesc: 'Calculation of Pool costs based on attributes and skill level',
    effectName: 'Cost calculation', calcWatch: 'costs', calcDefs: $scope.constants.resource_pools};

  EditorHelper.prepare(this, $scope)();

}]);


angular.module('lampost_editor').controller('DefenseEditorCtrl', ['$q', 'lmDialog', '$scope', 'EditorHelper',
  function ($q, lmDialog, $scope, EditorHelper) {

    this.modelList = {key: 'defense'};

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

    this.preCreate = function (defenseObj) {
      defenseObj.verb = defenseObj.dbo_id;
    };

    this.preUpdate = function () {
      if (!$scope.model.auto_start && !$scope.model.verb) {
        lmDialog.showOk("Start Method Required", "Either a command or 'autoStart' is required");
        return $q.reject();
      }
      return $q.when();
    };

    EditorHelper.prepare(this, $scope)();

  }]);


angular.module('lampost_editor').controller('RaceEditorCtrl', ['$scope', 'lmEditor', 'EditorHelper',
  function ($scope, lmEditor, EditorHelper) {

    this.modelList = {key: 'race'};

    $scope.defaultAttrsList = {listDesc: "Starting attributes for this race", listName: "Starting Attributes",
      attrWatch: 'base_attrs', attrDefs: $scope.constants.attr_map};

    this.preLoad = function () {
      return lmEditor.cache('allSkills').then(function (allSkills) {
        $scope.skillsList = {effectDesc: "Default skills and levels assigned to this race", effectName: "Default Skills",
          calcWatch: "default_skills", calcDefs: allSkills};
      })
    };

    EditorHelper.prepare(this, $scope)();

  }]);
