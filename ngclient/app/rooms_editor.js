angular.module('lampost_edit').controller('RoomsEditorController', ['$scope', 'lmRemote', 'lmEditor', 'lmDialog',
    function ($scope, lmRemote, lmEditor, lmDialog) {

        $scope.areaId = $scope.editor.parent;
        $scope.ready = false;
        loadRooms();

        function loadRooms() {
            lmRemote.request($scope.editor.url + "/list", {area_id:$scope.areaId}).then(function (rooms) {
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
        $scope.roomCreated = function (room) {
            $scope.rooms.push(room);
            sortRooms();
            $scope.editRoom(room);
        }
    }]);


angular.module('lampost_edit').controller('NewRoomController', ['$scope', 'lmRemote', 'parentScope', 'lmEditor', 'nextRoomId',
    function ($scope, lmRemote, parentScope, lmEditor, nextRoomId) {
        $scope.areaId = parentScope.areaId;
        $scope.newRoom = {id:nextRoomId, title:'', desc:''}
        $scope.createRoom = function () {
            lmRemote.request('editor/room/create', {area_id:$scope.areaId, room:$scope.newRoom}).then(function (room) {
                parentScope.roomCreated(room);
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


        function showResult(type, message) {
            $scope.showResult = true;
            $scope.resultMessage = message;
            $scope.resultType = 'alert-' + type;
        }

        $scope.roomId = $scope.editor.parent;
        $scope.ready = false;
        lmRemote.request($scope.editor.url + "/get", {room_id:$scope.roomId}).then(function (room) {
            if (room.basic.dbo_rev > $scope.editor.model_rev) {
                $scope.basic = room.basic;
                $scope.basic_copy = jQuery.extend(true, {}, room.basic);
                $scope.extras = room.extras;
                $scope.extras_copy = jQuery.extend(true, [], room.extras);
                $scope.exits = room.exits;
                $scope.exits_copy = jQuery.extend(true, [], room.exits);
                $scope.editor.copyToModel($scope);
                $scope.editor.model_rev = room.basic.dbo_rev;
            } else {
                $scope.editor.copyFromModel($scope);
            }
            $scope.ready = true;
        });

        $scope.updateBasic = function () {
            $scope.basic.desc = lmEditor.sanitize($scope.basic.desc);
            lmRemote.request($scope.editor.url + "/update_basic", $scope.basic).then(function (basic) {
                $scope.basic = basic;
                $scope.basic_copy = jQuery.extend(true, {}, basic);
                $scope.editor.copyToModel($scope);
                showResult("success", "Room basic information updated.");
            })
        };

        $scope.addNewExtra = function () {
            var newExtra = {title:"", desc:"", aliases:""};
            $scope.extras.push(newExtra);
            $scope.showDesc(newExtra);
            $timeout(function () {
                jQuery('.extra-title-edit:last').focus();
            })
        };

        $scope.deleteExtra = function (extraIx) {
            if ($scope.extras[extraIx] == $scope.currentExtra) {
                $scope.currentExtra = null;
            }
            $scope.extras.splice(extraIx, 1);
        };

        $scope.showDesc = function (extra) {
            $scope.currentExtra = extra;
            $scope.extraDisplay = 'desc';
        };

        $scope.newAlias = function () {
            $scope.currentExtra.editAliases.push({title:""});
            $timeout(function () {
                jQuery('.extra-alias-edit:last').focus();
            })
        };

        $scope.extraRowClass = function (extra) {
            if (extra == $scope.currentExtra) {
                return 'info';
            }
            return '';
        };

        $scope.deleteAlias = function (ix) {
            $scope.currentExtra.editAliases.splice(ix, 1);
        };

        $scope.revertExtras = function () {
            $scope.extras = jQuery.extend(true, [], $scope.extras_copy);
            $scope.editor.model.extras = $scope.extras;
            $scope.currentExtra = null;
        };

        $scope.updateExtras = function () {
            for (var i = 0; i < $scope.extras.length; i++) {
                var extra = $scope.extras[i];
                if (extra.hasOwnProperty('editAliases')) {
                    extra.aliases = [];
                    for (var j = 0; j < extra.editAliases.length; j++) {
                        var editAlias = extra.editAliases[j];
                        if (editAlias) {
                            extra.aliases.push(extra.editAliases[j].title);
                        }
                    }
                }
            }
            lmRemote.request($scope.editor.url + "/update_extras", {room_id:$scope.roomId, extras:$scope.extras})
                .then(function (extras) {
                    $scope.extras = extras;
                    $scope.extras_copy = jQuery.extend(true, [], extras);
                    $scope.editor.copyToModel($scope);
                    showResult("success", "Room extra descriptions updated.");
                });
        };

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
