angular.module('lampost_edit', []);

angular.module('lampost_edit').directive('editList', [function () {
    return {
        restrict:'A',
        require:'ngController',
        link:function (scope, element, attrs, ctrl) {
            ctrl.list_id = attrs.editList;
        }
    }
}]);

angular.module('lampost_edit').service('lmEditor', ['$q', 'lmBus', 'lmRemote', 'lmDialog', '$location', function ($q, lmBus, lmRemote, lmDialog, $location) {

    function Editor(type, parent) {
        var eType = this.types[type];
        this.label = eType.label ? eType.label : parent;
        this.label_class = parent ? "small" : "";
        this.controller = eType.controller;
        this.include = "view/editor/" + type + ".html";
        this.dirty = false;
        this.id = type + (parent ? ":" + parent : "");
        this.model = {};
        this.model_rev = -1;
        this.url = "editor/" + eType.url;
        this.parent = parent;
        this.type = type;
    }

    Editor.prototype.types = {
        config:{label:"Mud Config", url:"mud"},
        players:{label:"Players", url:"players"},
        areas:{label:"Areas", url:"area"},
        rooms:{label:"Rooms", url:"room"},
        room:{label:"", url:"room", model_props:['basic', 'extras', 'exits']}
    };

    Editor.prototype.copyFromModel = function (target) {
        var type = this.types[this.type];
        for (var i = 0; i < type.model_props.length; i++) {
            var prop = type.model_props[i];
            target[prop] = this.model[prop];
        }
    };

    Editor.prototype.copyToModel = function (source) {
        var type = this.types[this.type];
        for (var i = 0; i < type.model_props.length; i++) {
            var prop = type.model_props[i];
            this.model[prop] = source[prop];
        }
    };

    var self = this;
    var currentMap = {};
    this.areasMaster = {};
    this.roomsMaster = {};
    this.loadStatus = "loading";

    lmBus.register("login", configEditors);

    function configEditors(loginData) {
        self.editors = [];
        currentMap = {};
        var ids = loginData.editors;
        for (var i = 0; i < ids.length; i++) {
            var editor = new Editor(ids[i]);
            self.editors.push(editor);
            currentMap[editor.id] = editor;
        }
        self.currentEditor = self.editors[0];
        self.refreshData();
    }

    this.refreshData = function () {
        self.loadStatus = "loading";
        var areaPromise = lmRemote.request("editor/area/list").then(function (areas) {
            angular.forEach(areas, function (value) {
                self.areasMaster[value.id] = value;
            })
        });
        $q.all([areaPromise]).then(function () {
            self.loadStatus = "loaded";
            lmBus.dispatch('editor_change');
        });
    };

    this.addEditor = function (type, areaId) {
        var editor = new Editor(type, areaId);
        if (currentMap.hasOwnProperty(editor.id)) {
            editor = currentMap[editor.id];
        } else {
            currentMap[editor.id] = editor;
            self.editors.push(editor);
        }
        editor.prevEditor = self.currentEditor;
        self.currentEditor = editor;
        lmBus.dispatch('editor_change');
    };

    this.closeEditorId = function (editorId) {
        if (currentMap[editorId]) {
            self.closeEditor(currentMap[editorId])
        }
    };

    this.closeEditor = function (editor) {
        delete currentMap[editor.id];
        var ix = self.editors.indexOf(editor);
        self.editors.splice(ix, 1);
        if (editor == self.currentEditor) {
            var newEditor = editor.prevEditor;
            if (!currentMap[newEditor.id]) {
                newEditor = self.editors[0];
            }
            self.currentEditor = newEditor;
            lmBus.dispatch('editor_change');
        }
    };

    this.visitRoom = function (roomId) {
        lmRemote.request('editor/room/visit', {room_id:roomId}).then(function () {
            $location.path('game');
        })
    };

    this.deleteRoom = function (roomId) {
        lmDialog.showConfirm("Confirm Delete",
            "Are you sure you want to delete " + roomId + "?<br>(One way exits into this room will need to be deleted separately)",
            function () {
                lmRemote.request('editor/room/delete', {room_id:roomId}).then(function () {
                    var areaId = roomId.split(':')[0];
                    var rooms = self.roomsMaster[areaId];
                    angular.forEach(rooms, function (room, index) {
                        if (room.id == roomId) {
                            rooms.splice(index, 1);
                        }
                    });
                    self.closeEditorId('room:' + roomId);
                })
            }
        );
    };

    this.sanitize = function (text) {
        text = text.replace(/(\r\n|\n|\r)/gm, " ");
        return text.replace(/\s+/g, " ");
    };
}]);


angular.module('lampost_edit').controller('EditorController', ['$scope', 'lmEditor', 'lmBus', function ($scope, lmEditor, lmBus) {

    lmBus.register('editor_change', editorChange);

    $scope.editors = lmEditor.editors;
    editorChange();

    $scope.tabClass = function (editor) {
        return (editor == $scope.currentEditor ? "active " : " ") + editor.label_class;
    };

    function editorChange() {
        $scope.loadStatus = lmEditor.loadStatus;
        $scope.currentEditor = lmEditor.currentEditor;
    }

    $scope.click = function (editor) {
        lmEditor.lastEditor = lmEditor.currentEditor;
        $scope.currentEditor = editor;
        lmEditor.currentEditor = editor;
    };
    $scope.closeEditor = function (editor) {
        lmEditor.closeEditor(editor);
    };
}]);


angular.module('lampost_edit').controller('TableController', ['$scope', 'lmRemote', function ($scope) {
    var self = this;
    $scope.rowClass = function (rowForm) {
        if (rowForm.$invalid) {
            return 'error';
        }
        if (rowForm.$dirty) {
            return 'info';
        }
        return '';
    };

    $scope.revertRow = function (rowIx) {
        $scope[self.list_id][rowIx] = jQuery.extend(true, {}, $scope[self.list_id + '_copy'][rowIx]);
    };
    $scope.deleteRow = function (rowIx) {
        $scope[self.list_id + "Delete"](rowIx);
    };
    $scope.updateRow = function (rowIx) {
        $scope[self.list_id + "Update"](rowIx);
    }
}]);


angular.module('lampost_edit').controller('AreasEditorController', ['$scope', 'lmRemote', 'lmDialog', 'lmUtil', 'lmEditor',
    function ($scope, lmRemote, lmDialog, lmUtil, lmEditor) {

        $scope.areas = [];
        for (var areaId in lmEditor.areasMaster) {
            $scope.areas.push(lmEditor.areasMaster[areaId]);
        }
        lmUtil.stringSort($scope.areas, 'name');
        $scope.areas_copy = jQuery.extend(true, [], $scope.areas);

        $scope.showNewDialog = function () {
            lmDialog.show({templateUrl:"dialogs/newarea.html",
                controller:"NewAreaController", locals:{parentScope:$scope}})
        };

        $scope.addNew = function (newArea) {
            $scope.areas.push(newArea);
            lmUtil.stringSort($scope.areas, 'id');
            $scope.areas_copy.push(jQuery.extend(true, {}, newArea));
            lmEditors.areasMaster[newArea.id] = newArea;
        };

        $scope.areasDelete = function (rowIx) {
            var area = $scope.areas[rowIx];
            lmDialog.showConfirm("Confirm Delete",
                "Are you certain you want to delete area " + area.id + "?",
                function () {
                    lmRemote.request($scope.editor.url + "/delete", {areaId:area.id}).then(function (result) {
                        if (result == "OK") {
                            $scope.areas.splice(rowIx, 1);
                            $scope.areas_copy.splice(rowIx, 1);
                            delete lmEditor.areasMaster[area.id];
                        }
                    });
                });
        };

        $scope.areasUpdate = function (rowIx) {
            var area = $scope.areas[rowIx];
            lmRemote.request($scope.editor.url + "/update", {area:area}).then(function (result) {
                $scope.areas[rowIx] = result;
                $scope.areas_copy[rowIx] = jQuery.extends(true, {}, result);
            });
        };

        $scope.showRooms = function (area) {
            lmEditor.addEditor('rooms', area.id);
        };

    }]);


angular.module('lampost_edit').controller('NewAreaController', ['$scope', 'lmRemote', 'parentScope',
    function ($scope, lmRemote, parentScope) {

        $scope.newArea = {};
        $scope.areaExists = false;
        $scope.createArea = function () {
            lmRemote.request("editor/area/new", $scope.newArea).then(function (newAreaResult) {
                if (newAreaResult == "AREA_EXISTS") {
                    $scope.areaExists = true;
                } else {
                    $scope.dismiss();
                    parentScope.addNew(newAreaResult);
                }
            });
        };

    }]);


angular.module('lampost_edit').controller('MudConfigController', ['$scope', function ($scope) {
    $scope.data = '';
}]);