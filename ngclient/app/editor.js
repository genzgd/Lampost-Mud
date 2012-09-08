angular.module('lampost_edit', []);

angular.module('lampost_edit').directive('editList', [function() {
    return {
        restrict: 'A',
        require: 'ngController',
        link: function(scope, element, attrs, ctrl) {
            ctrl.list_id = attrs.editList;
        }
    }
}]);

angular.module('lampost_edit').service('lmEditor', ['lmBus', function(lmBus) {

    function Editor(type, parent) {

        var types = {
            config: {label: "Mud Config",  url:"mud"},
            players: {label: "Players",  url:"players"},
            areas: {label:"Areas", url:"area"}
        };

        var eType = types[type];

        this.label = eType.label + " " + (parent ? parent : "");
        this.controller = eType.controller;
        this.include = "view/editor/" + type + ".html";
        this.dirty = false;
        this.id = type + parent ? ":" + parent : "";
        this.model = {initialized: false};
        this.url = "editor/" + eType.url;
    }

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


angular.module('lampost_edit').controller('EditorController', ['$scope', 'lmEditor', function ($scope, lmEditor) {
    $scope.editors = lmEditor.editors;
    $scope.currentEditor = lmEditor.currentEditor;
    $scope.tabClass = function(editor) {
        return editor == $scope.currentEditor ? "active" : "";
    };

    $scope.click = function(editor) {
        $scope.currentEditor = editor;
        lmEditor.currentEditor = editor;
    }
}]);


angular.module('lampost_edit').controller('TableController', ['$scope', function($scope) {
    var self = this;
    $scope.rowClass = function(rowForm)  {
        if (rowForm.$invalid) {
            return 'error';
        }
        if (rowForm.$dirty) {
            return 'info';
        }
        return '';
    };

    $scope.revertRow = function(rowIx) {
        $scope[self.list_id][rowIx] = jQuery.extend(true, {}, $scope[self.list_id + '_copy'][rowIx]);
    };
}]);


angular.module('lampost_edit').controller('AreasEditorController', ['$scope', 'lmRemote', 'lmDialog',
    function ($scope, lmRemote, lmDialog) {
    this.editor = $scope.$parent.editor;
    $scope.model = this.editor.model;
    $scope.ready = false;
    var listPromise = lmRemote.request(this.editor.url + "/list").then(function(areas) {
        $scope.model.areas = areas;
        $scope.areas = areas;
        $scope.areas_copy = jQuery.extend(true, [], areas);
    });
    listPromise.then(function() {$scope.ready = true});
    $scope.addNew = function() {lmDialog.show({templateUrl:"dialogs/newarea.html"})};

}]);


angular.module('lampost_edit').controller('NewAreaController', ['$scope', function($scope) {
    $scope.createArea = function() {
        $scope.dismiss();
        alert("CREATING")
    };
}]);


angular.module('lampost_edit').controller('MudConfigController', ['$scope', function($scope) {
    $scope.data = '';
}]);
