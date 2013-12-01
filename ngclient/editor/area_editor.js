angular.module('lampost_editor').controller('AreaEditorCtrl', ['$scope', 'EditorHelper',
  function($scope, EditorHelper) {

    this.modelList = 'area';

    EditorHelper.prepareScope(this, $scope)();

  }]);

