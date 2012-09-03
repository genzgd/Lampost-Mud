angular.module('lampost').service('lmEditor', ['lmBus', function(lmBus) {

    var self = this;
    var labels = {config: "Mud Config", player: "players", area:"Area",
        user:"Users"};

    lmBus.register("login", configEditors);

    function configEditors(loginData) {
        self.editors = [];
        var ids = loginData.editors;

        for (var i = 0; i < ids.length; i++) {
            editors.push({id:ids[i], label:labels[ids[i]]});
        }
    }

}]);

function EditorController($scope, lmEditor) {
    $scope.buttons = [];
    for (var i = 0; i < lmEditor.editors.length; i++) {
        var editor = lmEditor.editors[i];
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
    $scope.data = '';
}
MudConfigController.$inject = ['$scope'];

function AreaEditorController($scope) {
    $scope.id = "Area1";
}
MudConfigController.$inject = ['$scope'];