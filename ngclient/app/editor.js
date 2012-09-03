function Editor(type, parent) {

    var types = {
        config: {label: "Mud Config", controller:MudConfigController},
        players: {label: "Players", controller:PlayersEditorController},
        areas: {label:"Areas", controller:AreasEditorController}
    };

    var eType = types[type];

    this.label = eType.label + " " + (parent ? parent : "");
    this.controller = eType.controller;
    this.include = "view/editor/" + type + ".html";
    this.dirty = false;
    this.id = type + parent ? ":" + parent : "";
    this.model = {initialized: false};

}

angular.module('lampost').directive('editorModel', [function() {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            scope.editor = scope.$eval(attrs.editorModel);
        }
    }
}]);

angular.module('lampost').service('lmEditor', ['lmBus', function(lmBus) {

    var self = this;

    lmBus.register("login", configEditors);

    function configEditors(loginData) {
        self.editors = [];

        var ids = loginData.editors;
        for (var i = 0; i < ids.length; i++) {
            self.editors.push(new Editor(ids[i]));
        }
        self.currentEditor = self.editors[0];
    }

}]);

function EditorController($scope, lmEditor) {
    $scope.editors = lmEditor.editors;
    $scope.currentEditor = lmEditor.currentEditor;
    $scope.tabClass = function(editor) {
        return editor == $scope.currentEditor ? "active" : "";
    };

    $scope.click = function(editor) {
        $scope.currentEditor = editor;
        lmEditor.currentEditor = editor;
    }
}
EditorController.$inject = ['$scope', 'lmEditor'];

function MudConfigController($scope) {
    $scope.data = '';
}
MudConfigController.$inject = ['$scope'];

function AreasEditorController($scope, lmRemote) {
    $scope.model = $scope.$parent.currentEditor.model;
    if (!$scope.model.initialized) {
        lmRemote.request("editor/area/list").then(function(list) {
            $scope.model.list = list;
            $scope.model.initialized = true;
        })
    }
}
AreasEditorController.$inject = ['$scope', 'lmRemote'];

function PlayersEditorController($scope) {

}
PlayersEditorController.$inject = ['$scope'];