angular.module('lampost_edit').controller('RoomsEditorController', ['$scope', 'lmRemote', 'lmEditor', 'lmDialog',
    function ($scope, lmRemote, lmEditor, lmDialog) {

        $scope.areaId = $scope.editor.parent;
        $scope.ready = false;
        loadRooms();

        function loadRooms() {
            lmEditor.loadRooms($scope.areaId).then(function(rooms) {
                $scope.rooms = rooms;
                $scope.ready = true;
            });
        }

        $scope.editRoom = function (room) {
            lmEditor.addEditor('room', room.id);
        };

        $scope.showNewDialog = function () {
            var area = lmEditor.areasMaster[$scope.areaId];
            lmDialog.show({templateUrl:"dialogs/new_room.html", controller:"NewRoomController",
                locals:{parentScope:$scope, nextRoomId:area.next_room_id}});
        };

        $scope.roomCreated = function (roomData) {
            var area = lmEditor.areasMaster[$scope.areaId];
            area.next_room_id = roomData.next_room_id;
            $scope.rooms.push(roomData.room);
            lmEditor.sortRooms($scope.areaId);
            $scope.editRoom(roomData.room);
        };

        $scope.deleteRoom = function(event, room) {
            event.preventDefault();
            event.stopPropagation();
            lmEditor.deleteRoom(room.id);
        };

        $scope.visitRoom = function(event, room) {
            event.preventDefault();
            event.stopPropagation();
            lmEditor.visitRoom(room.id);
        }
    }]);


angular.module('lampost_edit').controller('NewRoomController', ['$scope', 'lmRemote', 'parentScope', 'lmEditor', 'nextRoomId',
    function ($scope, lmRemote, parentScope, lmEditor, nextRoomId) {
        $scope.areaId = parentScope.areaId;
        $scope.newRoom = {id:nextRoomId, title:'', desc:''};
        $scope.createRoom = function () {
            lmRemote.request('editor/room/create', {area_id:$scope.areaId, room:$scope.newRoom}).then(function (roomData) {
                parentScope.roomCreated(roomData);
                $scope.dismiss();
            }, function (error) {
                if (error.data == "ROOM_EXISTS") {
                    $scope.roomExists = true;
                }
            })
        }
    }
]);

angular.module('lampost_edit').controller('RoomEditorController', ['$scope', 'lmRemote', 'lmEditor', '$timeout', 'lmDialog',
    function ($scope, lmRemote, lmEditor, $timeout, lmDialog) {

        var roomCopy = {};

        function showResult(type, message) {
            $scope.showResult = true;
            $scope.resultMessage = message;
            $scope.resultType = 'alert-' + type;
        }

        $scope.roomDirty = false;
        $scope.dirty = function() {
            $scope.roomDirty = true;
        };
        $scope.roomId = $scope.editor.parent;
        $scope.ready = false;
        $scope.directions = lmEditor.directions;
        lmRemote.request($scope.editor.url + "/get", {room_id:$scope.roomId}).then(function (room) {
            if (room.dbo_rev > $scope.editor.model_rev) {
                $scope.room = room;
                roomCopy = jQuery.extend(true, {}, room);
                $scope.editor.copyToModel($scope);
                $scope.editor.model_rev = room.dbo_rev;
            } else {
                $scope.editor.copyFromModel($scope);
            }
            $scope.ready = true;
        });

        $scope.deleteRoom = function() {
            lmEditor.deleteRoom($scope.roomId);
        };

        $scope.visitRoom = function() {
            lmEditor.visitRoom($scope.roomId);
        };

        $scope.updateRoom = function () {
            $scope.room.desc = lmEditor.sanitize($scope.room.desc);
            updateExtras();
            lmRemote.request($scope.editor.url + "/update", $scope.room).then(function (room) {
                roomCopy = jQuery.extend(true, {}, room);
                $scope.room = room;
                $scope.editor.copyToModel($scope);
                $scope.roomDirty = false;
                showResult("success", "Room data updated.");
            })
        };

        $scope.addNewExit = function() {
            lmDialog.show({templateUrl:"dialogs/new_exit.html", controller:"NewExitController",
                locals:{parentScope:$scope, roomId:$scope.roomId}});
        };

        $scope.addNewExtra = function () {
            var newExtra = {title:"", desc:"", aliases:""};
            $scope.room.extras.push(newExtra);
            $scope.showDesc(newExtra);
            $timeout(function () {
                jQuery('.extra-title-edit:last').focus();
            })
        };

        $scope.deleteExtra = function (extraIx) {
            if ($scope.room.extras[extraIx] == $scope.currentExtra) {
                $scope.currentExtra = null;
            }
            $scope.roomDirty = true;
            $scope.room.extras.splice(extraIx, 1);
        };

        $scope.showDesc = function (extra) {
            $scope.currentExtra = extra;
            $scope.extraDisplay = 'desc';
        };

        $scope.newAlias = function () {
            $scope.currentExtra.editAliases.push({title:""});
            $timeout(function () {
                jQuery('.extra-alias-edit:last').focus();
            });
        };

        $scope.extraRowClass = function (extra) {
            if (extra == $scope.currentExtra) {
                return 'info';
            }
            return '';
        };

        $scope.deleteAlias = function (ix) {
            $scope.roomDirty = true;
            $scope.currentExtra.editAliases.splice(ix, 1);
        };

        $scope.revertRoom = function () {
            $scope.room = roomCopy;
            $scope.currentExtra = null;
            $scope.roomDirty = false;
        };

        function updateExtras () {
            angular.forEach($scope.room.extras, function(extra) {
                if (extra.hasOwnProperty('editAliases')) {
                    extra.aliases = [];
                    angular.forEach(extra.editAliases, function(editAlias) {
                            if (editAlias) {
                                extra.aliases.push(editAlias.title)
                            }
                        }
                    )
                }
            })
        }

        $scope.showAliases = function (extra) {
            if (!extra.hasOwnProperty('editAliases')) {
                var editAliases = [];
                for (var i = 0; i < extra.aliases.length; i++) {
                    editAliases.push({title:extra.aliases[i]});
                }
                extra.editAliases = editAliases;
            }
            $scope.currentExtra = extra;
            $scope.extraDisplay = 'aliases';
        }

    }]);

angular.module('lampost_edit').controller('NewExitController', ['$scope', 'lmEditor', 'lmRemote', 'parentScope', 'roomId',
    function ($scope, lmEditor, lmRemote, parentScope, roomId) {

        var area;
        var roomAreaId;
        var roomList;
        var roomTitles;

        $scope.titleEdited = false;
        $scope.hasError = false;
        $scope.directions = lmEditor.directions;
        $scope.direction = $scope.directions[0];
        $scope.useNew = "new";
        $scope.areaList = [];
        angular.forEach(lmEditor.areasMaster, function (value, key) {
            $scope.areaList.push(key);
            $scope.areaList.sort();
        });

        $scope.changeType = function() {
            if ($scope.useNew == "existing") {
                $scope.titleEdited = false;
                refreshDestId();
            } else {
                $scope.hasError = false;
                $scope.destAreaId = roomAreaId;
                loadArea();
            }
        };

        $scope.changeId = function() {
            $scope.hasError = false;
            updateTitle();
        };

        $scope.changeArea = function() {
            loadArea($scope.destAreaId);
        };

        $scope.digExit = function() {
            alert("SUBMITTED");
        };

        roomAreaId = roomId.split(':')[0];
        $scope.destAreaId = roomAreaId;
        loadArea();

        function updateTitle() {
            $scope.hasError = false;
            if ($scope.useNew == "new") {
                if (!$scope.titleEdited) {
                    $scope.destTitle = area.name + " Room " + $scope.destId;
                }
                if (roomTitles[$scope.destId]) {
                    $scope.hasError = true;
                    $scope.lastError = "Room already exists";
                }
            } else {
                var roomTitle = roomTitles[$scope.destId];
                if (roomTitle) {
                    $scope.destTitle = roomTitle;
                } else {
                    $scope.destTitle = "";
                    $scope.hasError = true;
                    $scope.lastError = "Invalid Room";
                }
            }
        }

        function refreshDestId() {
            if ($scope.useNew == "new") {
                $scope.destId = area.next_room_id;
            } else {
                $scope.destId = parseInt(roomList[0].id.split(':')[1]);
            }
            updateTitle();
        }

        function loadArea() {
            area = lmEditor.areasMaster[$scope.destAreaId];
            lmEditor.loadRooms($scope.destAreaId).then(function(rooms) {
                roomList = rooms;
                roomTitles = {};
                angular.forEach(rooms, function (room) {
                    roomTitles[room.id.split(':')[1]] = room.title;
                });
                refreshDestId();
            })
        }



        /*$scope.newRoom = {id:nextRoomId, title:'', desc:''};
        $scope.createRoom = function () {
            lmRemote.request('editor/room/create', {area_id:$scope.areaId, room:$scope.newRoom}).then(function (roomData) {
                parentScope.roomCreated(roomData);
                $scope.dismiss();
            }, function (error) {
                if (error.data == "ROOM_EXISTS") {
                    $scope.roomExists = true;
                }
            })
        }*/
    }
]);