angular.module('lampost_editor').controller('RoomsEditorCtrl', ['$scope', 'lmRemote', 'lmEditor', 'lmDialog', 'lmBus',
    function ($scope, lmRemote, lmEditor, lmDialog, lmBus) {

        $scope.areaId = $scope.editor.parent;
        $scope.ready = false;
        loadRooms();

        lmBus.register('area_change', function() {}, $scope);
        lmBus.register('room_updated', function() {}, $scope);

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
            var area = lmEditor.getArea($scope.areaId);
            lmDialog.show({templateUrl:"editor/dialogs/new_room.html", controller:"NewRoomCtrl",
                locals:{parentScope:$scope, nextRoomId:area.next_room_id}});
        };

        $scope.roomCreated = function (roomData) {
            var area = lmEditor.getArea($scope.areaId);
            area.next_room_id = roomData.next_room_id;
            lmEditor.roomAdded(roomData.room);
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


angular.module('lampost_editor').controller('NewRoomCtrl', ['$scope', 'lmRemote', 'parentScope',  'nextRoomId',
    function ($scope, lmRemote, parentScope, nextRoomId) {
        $scope.areaId = parentScope.areaId;
        $scope.newRoom = {id:nextRoomId, title:'', desc:''};
        $scope.createRoom = function () {
            lmRemote.request('editor/room/create', {area_id:$scope.areaId, room:$scope.newRoom}).then(function (roomData) {
                parentScope.roomCreated(roomData);
                $scope.dismiss();
            }, function (error) {
                if (error.id == "RoomExists") {
                    $scope.roomExists = true;
                }
            })
        }
    }
]);

angular.module('lampost_editor').controller('RoomEditorCtrl', ['$scope', 'lmBus', 'lmRemote', 'lmEditor', '$timeout', 'lmDialog',
    function ($scope, lmBus, lmRemote, lmEditor, $timeout, lmDialog) {

        lmBus.register("exit_added", exitAdded);
        lmBus.register("exit_deleted", exitRemoved);
        lmBus.register("room_updated", roomUpdated);
        lmBus.register("mobile_updated", mobileUpdated);
        lmBus.register("mobile_deleted", mobileDeleted);
        lmBus.register("article_updated", articleUpdated);
        lmBus.register("article_deleted", articleDeleted);

        var roomCopy = {};
        $scope.roomDirty = false;
        $scope.dirty = function() {
            $scope.roomDirty = true;
            $scope.showResult = false;
        };
        $scope.roomId = $scope.editor.parent;
        $scope.directions = lmEditor.directions;
        var areaId = $scope.roomId.split(':')[0];

        updateData();
        function updateData() {
            $scope.ready = false;
            lmRemote.request($scope.editor.url + "/get", {room_id:$scope.roomId}).then(function (room) {
                if (room.dbo_rev > $scope.editor.model_rev) {
                    $scope.room = room;
                    roomCopy = angular.copy(room);
                    $scope.editor.copyToModel($scope);
                    $scope.editor.model_rev = room.dbo_rev;
                    lmEditor.updateRoom(room);
                } else {
                    $scope.editor.copyFromModel($scope);
                }
                $scope.ready = true;
            });
        }

        function showResult(type, message) {
            $scope.showResult = true;
            $scope.resultMessage = message;
            $scope.resultType = 'alert-' + type;
        }

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
                roomCopy = angular.copy(room);
                $scope.room = room;
                $scope.editor.copyToModel($scope);
                lmEditor.updateRoom(room);
                $scope.roomDirty = false;
                showResult("success", "Room data updated.");
            })
        };

        $scope.addNewExit = function() {
            lmDialog.show({templateUrl:"editor/dialogs/new_exit.html", controller:"NewExitCtrl",
                locals:{parentScope:$scope, roomId:$scope.roomId}});
        };

        $scope.deleteExit = function(exit, bothSides) {
            var exitData = {start_room:$scope.roomId, both_sides:bothSides,  dir:exit.dir};
            lmRemote.request($scope.editor.url + "/delete_exit", exitData).then(function(result) {
                    lmEditor.exitDeleted(result.exit);
                    result.other_exit && lmEditor.exitDeleted(result.other_exit);
                    result.room_deleted && lmEditor.roomDeleted(result.room_deleted);
                }
            )
        };

        $scope.addNewExtra = function () {
            var newExtra = {title:"", desc:"", aliases:""};
            $scope.room.extras.push(newExtra);
            $scope.showDesc(newExtra);
            $timeout(function () {
                jQuery('.extra-title-edit:last', '.' + $scope.editor.parentClass).focus();
            })
        };

        $scope.deleteExtra = function (extraIx) {
            if ($scope.room.extras[extraIx] == $scope.currentExtra) {
                $scope.currentExtra = null;
            }
            $scope.roomDirty = true;
            $scope.room.extras.splice(extraIx, 1);
        };

        $scope.addNewMobile = function() {
            lmDialog.show({templateUrl:"editor/dialogs/new_reset.html", controller:"NewResetCtrl",
                locals:{addFunc:addMobileReset, roomId:$scope.roomId, resetType:'Mobile', areaId: areaId}});
        };

        $scope.deleteMobile = function(mobileIx) {
            $scope.roomDirty = true;
            $scope.room.mobiles.splice(mobileIx);
        };

        $scope.mobileArticles = function(mobile) {
            lmDialog.show({templateUrl:"editor/dialogs/article_load.html", controller:"ArticleLoadCtrl",
                locals:{updateFunc:updateArticleLoads, reset:mobile, areaId: areaId}});
        };

        $scope.addNewArticle = function() {
            lmDialog.show({templateUrl:"editor/dialogs/new_reset.html", controller:"NewResetCtrl",
                locals:{addFunc:addArticleReset, roomId:$scope.roomId, resetType:'Article', areaId: areaId}});
        };

        $scope.deleteArticle = function(articleIx) {
            $scope.roomDirty = true;
            $scope.room.articles.splice(articleIx);
        };

        $scope.showDesc = function (extra) {
            $scope.currentExtra = extra;
            $scope.extraDisplay = 'desc';
        };

        $scope.newAlias = function () {
            $scope.currentExtra.editAliases.push({title:""});
            $timeout(function () {
                jQuery('.extra-alias-edit:last', '.' + $scope.editor.parentClass).focus();
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

        function exitAdded(exit) {
            if (exit.start_id == $scope.roomId) {
                $scope.room.exits.push(exit);
            }
        }

        function exitRemoved(exit) {
            if (exit.start_id == $scope.roomId) {
                angular.forEach($scope.room.exits.slice(), function(value, index) {
                    if (value.dir == exit.dir) {
                        $scope.room.exits.splice(index, 1);
                    }
                })
            }
        }

        function roomUpdated(room) {
            angular.forEach($scope.room.exits, function(exit) {
                if (exit.dest_id == room.id) {
                    exit.dest_title = room.title;
                    exit.dest_desc = room.desc;
                }
            });
        }

        function mobileUpdated(newmobile) {
            angular.forEach($scope.room.mobiles, function(mobile) {
               if (mobile.dbo.id == newmobile.dbo_id) {
                   mobile.title = newmobile.title;
                   mobile.desc = newmobile.desc;
               }
            });
        }

        function mobileDeleted(mobileId) {
            angular.forEach($scope.room.mobiles.slice(),  function(mobile) {
                if (mobile.dbo.id = mobileId) {
                    $scope.room.mobiles.splice($scope.room.mobiles.indexOf(mobile), 1);
                }
            });
            angular.forEach(roomCopy.mobiles.slice(), function(mobile) {
               if (mobile.dbo.id = mobileId) {
                   roomCopy.mobiles.splice(roomCopy.mobiles.indexOf(mobile), 1);
               }
            });
        }

        function articleUpdated(newarticle) {
            angular.forEach($scope.room.articles, function(article) {
                if (article.dbo_id == newarticle.dbo_id) {
                    article.title = newarticle.title;
                    article.desc = newarticle.desc;
                }
            });
        }

        function articleDeleted(articleId) {
            angular.forEach($scope.room.articles.slice(),  function(article) {
                if (article.dbo_id = articleId) {
                    $scope.room.articles.splice($scope.room.articles.indexOf(article), 1);
                }
            });
            angular.forEach(roomCopy.articles.slice(), function(article) {
                if (article.dbo_id = articleId) {
                    roomCopy.articles.splice(roomCopy.articles.indexOf(article), 1);
                }
            });
        }

        function updateExtras () {
            if ($scope.currentExtra && !$scope.currentExtra.title) {
                $scope.currentExtra = null;
            }
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
        };


        function addMobileReset(reset) {
            var newReset = {mobile_id:reset.object.dbo_id, mob_count:reset.count, mob_max:reset.max,
                title:reset.object.title, desc:reset.object.desc};
            $scope.room.mobiles.push(newReset);
            $scope.dirty();
        }

        function addArticleReset(reset) {
            var newReset = {article_id:reset.object.dbo_id, article_count:reset.count, article_max:reset.max,
                title:reset.object.title, desc:reset.object.desc};
            $scope.room.articles.push(newReset);
            $scope.dirty();
        }

        function updateArticleLoads() {
            $scope.dirty();
        }

    }]);

angular.module('lampost_editor').controller('NewExitCtrl', ['$scope', 'lmEditor', 'lmRemote', 'roomId',
    function ($scope, lmEditor, lmRemote, roomId) {

        var area;
        var roomAreaId;
        var roomList;
        var roomTitles;

        $scope.titleEdited = false;
        $scope.hasError = false;
        $scope.lastError = null;
        $scope.oneWay = false;
        $scope.directions = lmEditor.directions;
        $scope.direction = $scope.directions[0];
        $scope.useNew = "new";
        $scope.areaList = [];
        angular.forEach(lmEditor.areaList, function (value) {
            $scope.areaList.push(value.id);
        });
        $scope.areaList.sort();

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

        roomAreaId = roomId.split(':')[0];
        $scope.destAreaId = roomAreaId;
        loadArea();

        function updateTitle() {
            $scope.hasError = false;
            $scope.lastError = null;
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
            area = lmEditor.getArea($scope.destAreaId);
            lmEditor.loadRooms($scope.destAreaId).then(function(rooms) {
                roomList = rooms;
                roomTitles = {};
                angular.forEach(rooms, function (room) {
                    roomTitles[room.id.split(':')[1]] = room.title;
                });
                refreshDestId();
            })
        }

        $scope.digExit = function () {
            var newExit = {start_room:roomId, direction:$scope.direction.key, is_new:$scope.useNew == 'new',
                dest_area:$scope.destAreaId, dest_id:$scope.destId, one_way:$scope.oneWay,
                dest_title:$scope.destTitle};
            lmRemote.request('editor/room/create_exit', newExit).then(function (result) {
                lmEditor.exitAdded(result.exit);
                if (result.other_exit) {
                    lmEditor.exitAdded(result.other_exit);
                }
                if ($scope.useNew == 'new') {
                    area.next_room_id = result.next_room_id;
                    lmEditor.roomAdded(result.new_room)
                }
                $scope.dismiss();
            }, function (error) {
                $scope.lastError = error.text;
            })
        }
    }
]);

angular.module('lampost_editor').controller('NewResetCtrl', ['$scope', 'addFunc', 'roomId', 'resetType', 'lmEditor', 'areaId',
    function ($scope, addFunc, roomId, resetType, lmEditor, areaId) {

        var invalidObject = {dbo_id:'No ' + resetType + 's', title:'No ' + resetType + 's', desc:''};
        $scope.roomId = roomId;
        $scope.resetType = resetType;
        $scope.areaList = [];
        $scope.objects = [];
        $scope.disabled = true;
        angular.forEach(lmEditor.areaList, function (value) {
            $scope.areaList.push(value.id);
        });
        $scope.areaList.sort();
        $scope.areaId = areaId;
        $scope.reset = {count:1, max:1, object:invalidObject,  article_loads:[]};

        $scope.changeArea = function() {
            lmEditor.loadObjects(resetType.toLowerCase(), $scope.areaId).then(function(objects) {
               loadObjects(objects);
            });
        };

        $scope.changeArea();

        function loadObjects(objects) {
            if (objects.length == 0) {
                objects = [invalidObject];
                $scope.disabled = true;
            } else {
                $scope.disabled = false;
            }
            angular.forEach(objects, function(object) {
               object.objectId = object.dbo_id.split(':')[1];
            });
            $scope.objects = objects;
            $scope.reset.object = objects[0];
        }

        $scope.createReset = function() {
            addFunc($scope.reset);
            $scope.dismiss();
        };

}]);

angular.module('lampost_editor').controller('ArticleLoadCtrl', ['$scope', 'lmEditor', 'reset', 'areaId', 'updateFunc',
    function ($scope, lmEditor, reset, areaId, updateFunc) {

        $scope.areaList = [];
        angular.forEach(lmEditor.areaList, function (value) {
            $scope.areaList.push(value.id);
        });
        $scope.article_load_types = lmEditor.constants.article_load_types;
        $scope.articles = [];
        $scope.newArticle = {};
        $scope.addDisabled = true;
        $scope.reset = reset;
        $scope.areaList.sort();
        $scope.areaId = areaId;
        $scope.article_loads = angular.copy(reset.article_loads);


        $scope.changeArea = function() {
            lmEditor.loadObjects('article', $scope.areaId).then(function(articles) {
                loadObjects(articles);
            });
        };

        $scope.changeArea();

        function loadObjects(articles) {
            if (articles.length == 0) {
                $scope.articles = [{dbo_id:"No articles in area"}];
                $scope.addDisabled = true;
            } else {
                $scope.articles = articles;
                $scope.addDisabled = false;
            }
            $scope.newArticle = $scope.articles[0];
        }

        $scope.addArticleLoad = function() {
            var articleLoad = {article_id:$scope.newArticle.dbo_id, count: 1};
            if ($scope.newArticle.art_type == "weapon") {
                articleLoad.load_type = "equip";
                for (var i = 0; i < reset.article_loads.length; i++) {
                    if (reset.article_loads[i].load_type == 'equip') {
                        articleLoad.load_type = 'default';
                        break;
                    }
                }
            } else {
                articleLoad.load_type = "default";
            }
            $scope.article_loads.push(articleLoad);

        };

        $scope.deleteArticleLoad = function(articleIndex) {
            $scope.article_loads.splice(articleIndex, 1);
        };

        $scope.saveArticleLoads = function() {
            reset.article_loads = $scope.article_loads;
            updateFunc();
            $scope.dismiss();
        };



}]);
