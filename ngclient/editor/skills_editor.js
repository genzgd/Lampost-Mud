angular.module('lampost_editor').controller('AttackEditorCtrl', ['$scope', 'EditorHelper', function ($scope, EditorHelper) {

  EditorHelper.prepareScope(this, $scope);

  $scope.damageList = {inputDesc: 'Player Attribute', inputName: 'Attr', effectName: 'Damage',
    calcWatch: 'damage_calc', calcDefs: $scope.constants.calc_map};


}]);
