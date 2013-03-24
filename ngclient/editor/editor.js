angular.module('lampost_editor', ['lampost_svc', 'lampost_dir']);

angular.module('lampost_editor').run(['$timeout', 'lmUtil', 'lmEditor', 'lmRemote', function($timeout, lmUtil, lmEditor, lmRemote) {
    try {
        var playerId = name.split('_')[1];
        var sessionId = localStorage.getItem('lm_session_' + playerId);
        if (!sessionId) {
            throw ("No session found");
        }
        var editorList = $.parseJSON(localStorage.getItem('lm_editors_' + playerId));
        if (!editorList) {
            throw ("Invalid editor list");
        }
        lmRemote.childSession(sessionId);
        lmEditor.startEditors(editorList);
    } catch(e) {
        alert("No valid edit session:\n" + e);
        window.close();
    }
    window.editLampostRoom = function(roomId) {
        $timeout(function() {
            lmEditor.addEditor('room', roomId);}
        );
    }
}]);

angular.module('lampost_editor').directive('editList', [function () {
    return {
        restrict:'A',
        require:'ngController',
        link:function (scope, element, attrs, ctrl) {
            ctrl.list_id = attrs.editList;
        }
    }
}]);

angular.module('lampost_editor').service('lmEditor', ['$q', 'lmBus', 'lmRemote', 'lmDialog', '$location', 'lmUtil',
    function ($q, lmBus, lmRemote, lmDialog, $location, lmUtil) {

    var rawId = 0;
    var types = {
        config: {label:"Mud Config", url:"config"},
        players: {label:"Players", url:"player"},
        areas: {label:"Areas", url:"area"},
        rooms: {label:"Rooms", url:"room", childType:'mobile'},
        room: {label:"", url:"room", model_props:['room']},
        mobiles: {label:"Mobiles", url:'mobile', childType:'mobile'},
        mobile: {label:"", url:"mobile", model_props:['model'], newObject:{id:'', title:'', desc:'', level:1}},
        articles: {label:"Articles", url:"article", childType:'article'},
        article: {label:"", url:"article", model_props:['model'], newObject:{id:'', title:'', desc:'', level:1, weight: 1}},
        socials: {label:"Socials", url:"socials"},
        display: {label:"Display", url:"display"}
    };

    function Editor(type, parent) {
        var eType = types[type];
        this.label = eType.label ? eType.label : parent;
        this.label_class = parent ? "small" : "";
        this.controller = eType.controller;
        this.include = "editor/view/" + type + ".html";
        this.dirty = false;
        this.id = type + (parent ? ":" + parent : "");
        this.model = {};
        this.model_rev = -1;
        this.url = "editor/" + eType.url;
        this.parent = parent;
        this.type = type;
        this.childType = eType.childType;
        this.parentClass = "editor" + rawId++ + "parent";
    }

   Editor.prototype.copyFromModel = function (target) {
        var type = types[this.type];
        for (var i = 0; i < type.model_props.length; i++) {
            var prop = type.model_props[i];
            target[prop] = this.model[prop];
        }
    };

    Editor.prototype.copyToModel = function (source) {
        var type = types[this.type];
        for (var i = 0; i < type.model_props.length; i++) {
            var prop = type.model_props[i];
            this.model[prop] = source[prop];
        }
    };

    var self = this;
    var currentMap = {};
    var master = {};
    var areaMaster = {};

    this.areaList = [];
    this.roomsMaster = {};

    function idSort(values, field) {
        values.sort(function(a, b) {
            var aid = parseInt(a[field].split(':')[1]);
            var bid = parseInt(b[field].split(':')[1]);
            return aid - bid;
        })
    }

    this.startEditors = function (editorList) {
        self.editors = [];
        currentMap = {};
        var ids = editorList;
        for (var i = 0; i < ids.length; i++) {
            var editor = new Editor(ids[i]);
            self.editors.push(editor);
            currentMap[editor.id] = editor;
        }
        self.currentEditor = self.editors[0];
        self.refreshData();
    };

    this.refreshData = function () {
        self.loadStatus = "loading";
        master = {};
        master.mobile = {};
        master.item = {};
        master.article = {};
        self.areaList = [];
        self.roomsMaster = {};
        $q.all([
            lmRemote.request('editor/area/list').then(function (areas) {
                angular.forEach(areas, function (value) {
                    areaMaster[value.id] = value;
                    self.areaList.push(value);
                })
            }),
            lmRemote.request('editor/room/dir_list').then(function (directions) {
                self.directions = directions;
            }),
            lmRemote.request('editor/constants').then( function(constants) {
                self.constants = constants;
            })
        ]).then(function () {
            lmUtil.stringSort(self.areaList, 'name');
            self.loadStatus = "loaded";
            var roomId = localStorage.getItem("editor_room_id");
            if (roomId) {
                localStorage.removeItem("editor_room_id");
                self.addEditor('room', roomId);
            } else {
                lmBus.dispatch('editor_change');
            }
            lmBus.dispatch('editor_ready');
        });
    };

    this.addEditor = function (type, parent) {
        var editor = new Editor(type, parent);
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

    this.getArea = function(areaId) {
        return areaMaster[areaId];
    };

    this.visitRoom = function (roomId) {
        lmRemote.request('editor/room/visit', {room_id:roomId});
        window.open("",window.opener.name);
    };

    this.loadRooms = function(areaId) {
        var rooms = self.roomsMaster[areaId];
        if (rooms) {
            var deferred = $q.defer();
            deferred.resolve(rooms);
            return deferred.promise;
        }
        return lmRemote.request('editor/room/list', {area_id:areaId}, true).then(function (rooms) {
            idSort(rooms,  'id');
            self.roomsMaster[areaId] = rooms;
            return rooms;
        });
    };

    this.loadObjects = function(type, areaId) {
        var objects = master[type][areaId];
        if (objects) {
            var deferred = $q.defer();
            deferred.resolve(objects);
            return deferred.promise;
        }
        return lmRemote.request('editor/' + type + '/list', {area_id:areaId}, true).then(function (objects) {
            master[type][areaId] = objects;
            lmUtil.stringSort(objects, 'dbo_id');
            return objects;
        });
    };

    this.objectAdded = function(type, object) {
        var areaId = object.dbo_id.split(':')[0];
        master[type][areaId].push(object);
        lmUtil.stringSort(master[type][areaId], 'dbo_id');
        areaMaster[areaId][type] = master[type][areaId].length;
    };

    this.roomAdded = function(room) {
        var areaId = room.id.split(':')[0];
        self.roomsMaster[areaId].push(room);
        idSort(self.roomsMaster[areaId],  'id');
        areaMaster[areaId].room = self.roomsMaster[areaId].length;
        lmBus.dispatch('area_change', areaId);
    };

    this.exitAdded = function(exit) {
        lmBus.dispatch("exit_added", exit);
        var areaId = exit.start_id.split(':')[0];
        angular.forEach(self.roomsMaster[areaId], function(value) {
            if (value.id == exit.start_id) {
                value.exit_count++;
            }
        })
    };

    this.exitDeleted = function(exit) {
        lmBus.dispatch("exit_deleted", exit);
        var areaId = exit.start_id.split(':')[0];
        angular.forEach(self.roomsMaster[areaId], function(value) {
            if (value.id == exit.start_id) {
                value.exit_count--;
            }
        })
    };

    this.roomDeleted = function(roomId) {
        var areaId = roomId.split(':')[0];
        var rooms = self.roomsMaster[areaId];
        if (rooms) {
            angular.forEach(rooms.slice(), function(value, index) {
                if (value.id == roomId) {
                    rooms.splice(index, 1);
                    lmBus.dispatch('area_change', areaId);
                }
            });
            areaMaster[areaId].room = rooms.length;
        }
        self.closeEditorId('room:' + roomId);
    };

    function objectDeleted(type, objectId) {
        var areaId = objectId.split(':')[0];
        var objects = master[type][areaId];
        if (objects) {
            angular.forEach(objects.slice(), function(object) {
                if (object.dbo_id == objectId) {
                    objects.splice(objects.indexOf(object), 1);
                    lmBus.dispatch('area_change', areaId);
                }
            });
            areaMaster[areaId][type] = objects.length;
        }
        self.closeEditorId(type + ':' + objectId);
        lmBus.dispatch(type + "_deleted", objectId);
    }

    this.deleteRoom = function (roomId) {
        lmDialog.showConfirm("Confirm Delete",
            "Are you sure you want to delete " + roomId + "?<br>(One way exits into this room will need to be deleted separately)",
            function () {
                lmRemote.request('editor/room/delete', {room_id:roomId}).then(function (deleted_exits) {
                    var areaId = roomId.split(':')[0];
                    var rooms = self.roomsMaster[areaId];
                    angular.forEach(rooms.slice(), function (room, index) {
                        if (room.id == roomId) {
                            rooms.splice(index, 1);
                        }
                    });
                    angular.forEach(deleted_exits, function(exit) {
                        self.exitDeleted(exit);
                    });
                    self.closeEditorId('room:' + roomId);
                })
            }
        );
    };

    this.deleteObject = function(type, objectId) {
        lmDialog.showConfirm("Confirm Delete",
            "Are you sure you want to delete " + objectId + "?", function() {
            lmRemote.request('editor/' + type + '/delete', {object_id:objectId, force:false}).then(function ()
                    {objectDeleted(type, objectId);},
                function(error) {
                    if (error.data == 'IN_USE') {
                        lmDialog.showConfirm('Object in Use', 'This ' + type + ' is in use.  Delete anyway?', function () {
                            lmRemote.request('editor/' + type + '/delete', {object_id:objectId, force:true}).then( function() {
                                objectDeleted(type, objectId);
                            });
                        });
                    }
                }
            )}
        )
    };

    this.addArea = function(area) {
        areaMaster[area.id] = area;
        self.areaList.push(area);
        lmUtil.stringSort(self.areaList, 'name');
    };

    this.deleteArea = function(areaId) {
        delete areaMaster[areaId];
        angular.forEach(master, function(value, key) {
            delete master[key];
        });
        delete self.roomsMaster[areaId];
        angular.forEach(self.areaList, function(area, index) {
           if (area.id == areaId) {
               self.areaList.splice(index, 1);
           }
        });
        angular.forEach(self.editors.slice(), function(editor) {
            if (editor.parent && (editor.parent == areaId || editor.parent.split(':')[0] == areaId)) {
                self.closeEditor(editor);
            }
        })
    };

    this.updateRoom = function(room) {
        var areaId = room.id.split(':')[0];
        angular.forEach(self.roomsMaster[areaId], function(roomStub) {
           if (roomStub.id == room.id) {
               roomStub.title = room.title;
               roomStub.extra_count = room.extras.length;
               roomStub.mobile_count = room.mobiles.length;
           }
        });
        lmBus.dispatch("room_updated", room);
    };

    this.newObject = function(type) {
        return jQuery.extend(true, {}, types[type].newObject);
    };

    this.updateObject = function(type, object) {
        var areaId = object.dbo_id.split(':')[0];
        var objects = master[type][areaId];
        if (objects) {
            angular.forEach(objects.slice(), function(existing, index) {
                if (existing.dbo_id == object.dbo_id) {
                    objects[index] = object;
                }
            })
        }
        lmBus.dispatch(type + '_updated', object);
    };

    this.sanitize = function (text) {
        text = text.replace(/(\r\n|\n|\r)/gm, " ");
        return text.replace(/\s+/g, " ");
    };
}]);


angular.module('lampost_editor').controller('EditorController', ['$scope', 'lmEditor', 'lmBus', function ($scope, lmEditor, lmBus) {

    lmBus.register('editor_change', editorChange);
    lmBus.register('editor_ready', editorReady);

    $scope.editors = lmEditor.editors;
    editorChange();

    $scope.tabClass = function (editor) {
        return (editor == $scope.currentEditor ? "active " : " ") + editor.label_class;
    };

    function editorReady() {
        $scope.constants = lmEditor.constants;
        $scope.loadStatus = lmEditor.loadStatus;
    }

    function editorChange() {
        $scope.currentEditor = lmEditor.currentEditor;
        lmBus.dispatch('editor_activated', $scope.currentEditor);
    }

    $scope.click = function (editor) {
        lmEditor.lastEditor = lmEditor.currentEditor;
        $scope.currentEditor = editor;
        lmEditor.currentEditor = editor;
        lmBus.dispatch('editor_activated', editor);
    };
    $scope.closeEditor = function (editor) {
        lmEditor.closeEditor(editor);
    };

    $scope.addEditor = function(type, parent) {
        lmEditor.addEditor(type, parent);
    }
}]);


angular.module('lampost_editor').controller('TableController', ['$scope', 'lmRemote', function ($scope) {
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
        $scope[self.list_id + "Revert"](rowIx);
    };
    $scope.deleteRow = function (rowIx) {
        $scope[self.list_id + "Delete"](rowIx);
    };
    $scope.updateRow = function (rowIx) {
        $scope[self.list_id + "Update"](rowIx);
    }
}]);


angular.module('lampost_editor').controller('AreasEditorController', ['$scope', 'lmRemote', 'lmDialog', 'lmUtil', 'lmEditor',
    function ($scope, lmRemote, lmDialog, lmUtil, lmEditor) {

        var originals = {};
        function updateOriginal(area) {
            originals[area.id] = jQuery.extend(true, {}, area);
        }
        $scope.areas = lmEditor.areaList;
        angular.forEach($scope.areas, updateOriginal);

        $scope.showNewDialog = function () {
            lmDialog.show({templateUrl:"editor/dialogs/new_area.html",
                controller:"NewAreaController", locals:{parentScope:$scope}})
        };

        $scope.addNew = function (newArea) {
            lmEditor.addArea(newArea);
            updateOriginal(newArea);
        };

        $scope.areasRevert = function (rowIx) {
            $scope.areas[rowIx] = jQuery.extend(true, {}, originals[$scope.areas[rowIx].id]);
        };

        $scope.areasDelete = function (rowIx) {
            var area = $scope.areas[rowIx];
            lmDialog.showConfirm("Confirm Delete",
                "Are you certain you want to delete area " + area.id + "?",
                function () {
                    lmRemote.request($scope.editor.url + "/delete", {areaId:area.id}).then(function () {
                        lmEditor.deleteArea(area.id);
                        delete originals[area.id];
                    });
                });
        };

        $scope.areasUpdate = function (rowIx) {
            var area = $scope.areas[rowIx];
            lmRemote.request($scope.editor.url + "/update", {area:area}).then(function (result) {
                $scope.areas[rowIx] = result;
                lmUtil.stringSort($scope.areas, 'name');
                updateOriginal(result);
            });
        };

    }]);


angular.module('lampost_editor').controller('NewAreaController', ['$scope', 'lmRemote', 'parentScope',
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


angular.module('lampost_editor').controller('MudConfigController', ['$rootScope', '$scope', 'lmBus', 'lmRemote', 'lmEditor', '$timeout',
    function ($rootScope, $scope, lmBus, lmRemote, lmEditor, $timeout) {

    var configCopy;
    $scope.ready = false;
    $scope.areaList = [];
    angular.forEach(lmEditor.areaList, function (value) {
        $scope.areaList.push(value.id);
        $scope.areaList.sort();
    });
    if (lmEditor.currentEditor == $scope.editor) {
        loadConfig();
    }

    $scope.changeArea = function() {
        lmEditor.loadRooms($scope.startAreaId).then(function(rooms) {
            $scope.rooms = [];
            $scope.startRoom = null;
            angular.forEach(rooms, function(room) {
                var roomStub = {id:room.id, label:room.id.split(':')[1] + ': ' + room.title};
                $scope.rooms.push(roomStub);
                if (roomStub.id == $scope.config.start_room) {
                    $scope.startRoom = roomStub;
                }
            });
            if (!$scope.startRoom) {
                $scope.startRoom = $scope.rooms[0];
            }
            $scope.ready = true;
        });
    };
    lmBus.register("editor_activated", function(editor) {
        if (editor == $scope.editor) {
            loadConfig();
        }
    });

    $scope.updateConfig = function() {
        $scope.config.start_room = $scope.startRoom.id;
        lmRemote.request($scope.editor.url + "/update", {config:$scope.config}).then(function(config) {
            prepare(config);
            lampost_config.title = config.title;
            lampost_config.description = config.description;
            $timeout(function() {
                $rootScope.siteTitle = config.title;
            });
            $('title').text(lampost_config.title);
        });
    };

    $scope.revertConfig = function() {
        $scope.config = configCopy;
        $scope.startAreaId = $scope.config.start_room.split(':')[0];
        $scope.changeArea();
    };

    function loadConfig() {
        lmRemote.request($scope.editor.url + "/get").then(prepare);
    }

    function prepare(config) {
        configCopy = jQuery.extend(true, {}, config);
        $scope.config = config;
        $scope.startAreaId = config.start_room.split(':')[0];
        $scope.changeArea();
    }

}]);
