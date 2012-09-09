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


angular.module('lampost_edit').controller('TableController', ['$scope', 'lmRemote', function($scope) {
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
    $scope.deleteRow = function(rowIx) {
        $scope[self.list_id + "Delete"](rowIx);
    };
    $scope.updateRow = function(rowIx) {
        $scope[self.list_id + "Update"](rowIx);
    }
}]);


angular.module('lampost_edit').controller('AreasEditorController', ['$scope', 'lmRemote', 'lmDialog', 'lmArrays',
    function ($scope, lmRemote, lmDialog, lmArrays) {

    $scope.editor = $scope.currentEditor;
    $scope.model = $scope.editor.model;
    $scope.ready = false;
    var listPromise = lmRemote.request($scope.editor.url + "/list").then(function(areas) {
        lmArrays.stringSort(areas, 'id');
        $scope.model.areas = areas;
        $scope.areas = areas;
        $scope.areas_copy = jQuery.extend(true, [], areas);
    });
    listPromise.then(function() {$scope.ready = true});
    $scope.showNewDialog = function() {lmDialog.show({templateUrl:"dialogs/newarea.html",
        controller:"NewAreaController", locals:{parentScope:$scope}})};

    $scope.addNew = function (newArea) {
        $scope.areas.push(newArea);
        lmArrays.stringSort($scope.areas, 'id');
        $scope.areas_copy.push(jQuery.extend(true, {}, newArea));
    };

    $scope.areasDelete = function(rowIx) {
        var area = $scope.areas[rowIx];
        lmDialog.showConfirm("Confirm Delete",
            "Are you certain you want to delete area " + area.id + "?",
            function() {
                lmRemote.request($scope.editor.url + "/delete", {areaId:area.id}).then(function(result) {
                if (result == "OK") {
                    $scope.areas.splice(rowIx,  1);
                    $scope.areas_copy.splic(rowIx, 1);
                }
            });
        });
    };

    $scope.areasUpdate = function(rowIx) {
        var area = $scope.areas[rowIx];
        lmRemote.request($scope.editor.url + "/update", {area:area}).then(function(result) {
            $scope.areas[rowIx] = result;
            $scope.areas_copy[rowIx] = jQuery.extends(true, {}, result);
        });
    }

}]);


angular.module('lampost_edit').controller('NewAreaController', ['$scope', 'lmRemote', 'parentScope',
    function($scope, lmRemote, parentScope) {

    $scope.newArea = {};
    $scope.areaExists = false;
    $scope.createArea = function() {
        lmRemote.request("editor/area/new", $scope.newArea).then(function(newAreaResult) {
            if (newAreaResult == "AREA_EXISTS") {
                $scope.areaExists = true;
            } else {
                $scope.dismiss();
                parentScope.addNew(newAreaResult);
            }
        });
    };

}]);


angular.module('lampost_edit').controller('MudConfigController', ['$scope', function($scope) {
    $scope.data = '';
}]);
