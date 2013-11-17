angular.module('lampost_editor').controller('AttackEditorCtrl', ['$scope', 'EditorHelper', function ($scope, EditorHelper) {

  EditorHelper.prepareScope(this, $scope);

  $scope.damageList = {effectDesc: 'Calculation of Damage based on attributes and roll', effectName: 'Damage Calculation',
    calcWatch: 'damage_calc', calcDefs: $scope.constants.calc_map};

   $scope.accuracyList = {effectDesc: 'Calculation of Accuracy based on attributes and roll', effectName: 'Accuracy Calculation',
    calcWatch: 'accuracy_calc', calcDefs: $scope.constants.calc_map};

  $scope.costList = {effectDesc: 'Calculation of Pool costs based on attributes and skill level',
    effectName: 'Cost calculation', calcWatch: 'costs', calcDefs: $scope.constants.resource_pools}
}]);
