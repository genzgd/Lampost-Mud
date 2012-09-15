angular.module('lampost_edit').controller('RoomsEditorController', ['$scope', 'lmRemote', 'lmEditor', 'lmDialog',
    function ($scope, lmRemote, lmEditor, lmDialog) {

        $scope.areaId = $scope.editor.parent;
        $scope.ready = false;
        loadRooms();

        function loadRooms() {
            lmRemote.request($scope.editor.url + "/list", {area_id:$scope.areaId}).then(function (rooms) {
                lmEditor.roomsMaster[$scope.areaId] = rooms;
                $scope.rooms = rooms;
                sortRooms();
                $scope.ready = true;
            });
        }

        function sortRooms() {
            $scope.rooms.sort(function(a, b) {
                var aid = parseInt(a.id.split(':')[1]);
                var bid = parseInt(b.id.split(':')[1]);
                return aid - bid;
            });
        }

        $scope.editRoom = function (room) {
            lmEditor.addEditor('room', room.id);
        };
        $scope.showNewDialog = function () {
            var area = lmEditor.areasMaster[$scope.areaId];
            if (area) {
                lmDialog.show({templateUrl:"dialogs/new_room.html", controller:"NewRoomController",
                    locals:{parentScope:$scope, nextRoomId:area.next_room_id}});
            } else {
                lmDialog.showOk("Area invalid");
                lmEditor.closeEditor($scope.editor);
            }
        };

        $scope.roomCreated = function (roomData) {
            var area = lmEditor.areasMaster[$scope.areaId];
            area.next_room_id = roomData.next_room_id;
            $scope.rooms.push(roomData.room);
            sortRooms();
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

angular.module('lampost_edit').controller('RoomEditorController', ['$scope', 'lmRemote', 'lmEditor', '$timeout',
    function ($scope, lmRemote, lmEditor, $timeout) {

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
