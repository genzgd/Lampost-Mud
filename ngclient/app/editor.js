angular.module('lampost').service('lmEditor', [function() {
    this.editors = {};
    this.editors.config = {id:"config", label: "Mud Config", controller:MudConfigController};
    this.editors.players = {id:"players", label: "Players"};
    this.editors.area = {id:"area", label:"Area"}
}]);

function EditorController($scope, lmEditor) {
    $scope.buttons = [];
    for (var i = 0; i < $scope.editors.length; i++) {
        var editor = lmEditor.editors[$scope.editors[i]];
        editor.dirty = false;
        editor.class = function() {
            return (this == $scope.editor) ? "active" : "";
        };
        $scope.buttons.push(editor);
    }
    $scope.editor = $scope.buttons[0];
    $scope.click = function(editor) {
        $scope.editor = editor;
    }
}
EditorController.$inject = ['$scope', 'lmEditor'];

function MudConfigController($scope) {

}
MudConfigController.$inject = ['$scope'];

function AreaEditorController($scope) {
    $scope.id = "Area1";
}
MudConfigController.$inject = ['$scope'];