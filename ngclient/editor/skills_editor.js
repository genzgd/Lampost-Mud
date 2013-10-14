angular.module('lampost_editor').controller('AttackEditorCtrl', ['$scope', 'EditorHelper', function ($scope, EditorHelper) {

  EditorHelper.prepareScope(this, $scope);

   function removeNulls() {
     angular.forEach($scope.activeObject.accuracy_calc, function(value, key) {
      if (!value) {
        delete $scope.activeObject[key]
      }
    });

     angular.forEach($scope.activeObject.damage_calc, function(value, key) {
      if (!value) {
        delete $scope.activeObject[key]
      }
    });

  }

  this.preUpdate = function() {
    removeNulls();
  };

  this.preCreate = function() {
    removeNulls();
  };

}]);
