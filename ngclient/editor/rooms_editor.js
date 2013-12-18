angular.module('lampost_editor').controller('RoomEditorCtrl', ['$q', '$scope', 'lmBus', 'lmRemote', 'lmEditor', '$timeout', 'lmDialog',
  function ($q, $scope, lmBus, lmRemote, lmEditor, $timeout, lmDialog) {

    var self = this;
    var areaId = null;
    var cacheKeys = [];
    var dirMap = {};

    this.startEdit = function (model) {
      areaId = model.dbo_id.split(':')[0];
    };

    var originalModel = lmEditor.prepare(this, $scope).originalModel;

    function addRoomRef(roomId) {
      var areaId = roomId.split(":")[0];
      var roomKey = 'room:' + areaId;
      if (cacheKeys.indexOf(roomKey) == -1) {
        cacheKeys.push(roomKey);
        return lmEditor.cache(roomKey);
      }
      return $q.when()
    }

    this.startEdit = function (room) {
      $scope.currentExtra = null;
      $scope.extraDisplay = 'desc';
      lmEditor.cache("constants").then(function (constants) {
        angular.forEach(constants.directions, function (dir) {
          dirMap[dir.key] = dir;
        });
      });
      angular.forEach(cacheKeys, function (key) {
        lmEditor.deref(key);
      });
      cacheKeys = [];
      var editPromises = [];
      angular.forEach(room.exits, function (exit) {
        editPromises.push(addRoomRef(exit.destination));
      });
      return $q.all(editPromises);
    };

    this.postDelete = function(model) {
      $scope.startEditor('area');
    };

    $scope.editor.newEdit($scope.editor.editModel);

    this.addExit = function (exit) {
      originalModel().exits.push(exit);
      addRoomRef(exit.destination);
    };

    $scope.visitRoom = function () {
      lmEditor.visitRoom($scope.model.dbo_id);
    };

    $scope.exitRoom = function (exit) {
      var destKey = 'room:' + exit.destination.split(':')[0];
      return lmEditor.cacheValue(destKey, exit.destination);
    };

    $scope.exitTwoWay = function (exit) {
      var otherExits = $scope.exitRoom(exit).exits;
      var rev_key = dirMap[exit.dir_name].rev_key;
      for (var i = 0; i < otherExits.length; i++) {
        var otherExit = otherExits[i];
        if (otherExit.dir_name === rev_key && otherExit.destination === $scope.model.dbo_id) {
          return true;
        }
      }
      return false;
    };

    $scope.addNewExit = function () {
      lmDialog.show({templateUrl: "editor/dialogs/new_exit.html", controller: "NewExitCtrl",
        locals: {roomController: self, room: $scope.model}});
    };

    $scope.deleteExit = function (exit, bothSides) {
      lmDialog.showConfirm("Delete Exit", "Are you sure you want to delete this exit", function () {
        lmRemote.request("editor/room/delete_exit",
          {start_room: $scope.model.dbo_id, both_sides: bothSides, dir: exit.dir_name}).then(function () {
            var exitLoc = $scope.model.exits.indexOf(exit);
            if (exitLoc > -1) {
              $scope.model.exits.splice(exitLoc, 1);
            }
            var originalExits = originalModel().exits;
            for (var i = 0; i < originalExits.length; i++) {
              if (originalExits[i].dir === exit.dir) {
                originalExits.splice(i, 1);
                break;
              }
            }
          }
        )
      })
    };

    $scope.addNewExtra = function () {
      var newExtra = {title: "", desc: "", aliases: []};
      $scope.model.extras.push(newExtra);
      $scope.showDesc(newExtra);
      $timeout(function () {
        jQuery('.extra-title-edit:last').focus();
      })
    };

    $scope.deleteExtra = function (extraIx) {
      if (angular.equals($scope.currentExtra, $scope.model.extras[extraIx])) {
        $scope.currentExtra = null;
      }
      $scope.model.extras.splice(extraIx, 1);
    };

    $scope.addNewMobile = function () {
      lmDialog.show({templateUrl: "editor/dialogs/new_reset.html", controller: "NewResetCtrl",
        locals: {addFunc: addMobileReset, roomId: $scope.roomId, resetType: 'Mobile', areaId: areaId}});
    };

    $scope.deleteMobile = function (mobileIx) {
      $scope.room.mobiles.splice(mobileIx);
    };

    $scope.mobileArticles = function (mobile) {
      lmDialog.show({templateUrl: "editor/dialogs/article_load.html", controller: "ArticleLoadCtrl",
        locals: {updateFunc: updateArticleLoads, reset: mobile, areaId: areaId}});
    };

    $scope.addNewArticle = function () {
      lmDialog.show({templateUrl: "editor/dialogs/new_reset.html", controller: "NewResetCtrl",
        locals: {addFunc: addArticleReset, roomId: $scope.roomId, resetType: 'Article', areaId: areaId}});
    };

    $scope.deleteArticle = function (articleIx) {
      $scope.room.articles.splice(articleIx);
    };

    $scope.showDesc = function (extra) {
      $scope.currentExtra = extra;
      $scope.extraDisplay = 'desc';
    };

    $scope.newAlias = function () {
      $scope.currentExtra.aliases.push("");
      $timeout(function () {
        jQuery('.extra-alias-edit:last').focus();
      });
    };

    $scope.extraRowClass = function (extra) {
      return extra === $scope.currentExtra ? 'info' : '';
    };

    $scope.deleteAlias = function (ix) {
      $scope.currentExtra.aliases.splice(ix, 1);
    };

    $scope.showAliases = function (extra) {
      $scope.currentExtra = extra;
      $scope.extraDisplay = 'aliases';
    };

    function addMobileReset(reset) {
      var newReset = {mobile_id: reset.object.dbo_id, mob_count: reset.count, mob_max: reset.max,
        title: reset.object.title, desc: reset.object.desc};
      $scope.room.mobiles.push(newReset);
    }

    function addArticleReset(reset) {
      var newReset = {article_id: reset.object.dbo_id, article_count: reset.count, article_max: reset.max,
        title: reset.object.title, desc: reset.object.desc};
      $scope.room.articles.push(newReset);
    }

    function updateArticleLoads() {
      $scope.dirty();
    }

  }]);

angular.module('lampost_editor').controller('NewExitCtrl', ['$q', '$scope', 'lmEditor', 'lmRemote', 'roomController', 'room',
  function ($q, $scope, lmEditor, lmRemote, roomController, room) {

    var area;
    var listKey;
    var prevDestId;

    var roomAreaId = room.dbo_id.split(':')[0];
    var newRoom = {};

    $scope.hasError = false;
    $scope.lastError = null;
    $scope.oneWay = false;
    $scope.destAreaId = roomAreaId;

    $q.all([
      lmEditor.cache('constants').then(function (constants) {
        $scope.directions = constants.directions;
        $scope.direction = $scope.directions[0];
      }),
      lmEditor.cache('area').then(function (areas) {
        $scope.areaList = areas;
        area = lmEditor.cacheValue('area', roomAreaId);
        newRoom.title = area.name + " Room " + area.next_room_id;
        newRoom.destId = area.next_room_id;
        prevDestId = newRoom.destId;
      })]).then(loadArea);

    $scope.useNew = true;

    $scope.changeType = function () {
      $scope.hasError = false;
      if ($scope.useNew) {
        $scope.destRoom = newRoom;
        if ($scope.destAreaId !== roomAreaId) {
          $scope.destAreaId = roomAreaId;
          loadArea();
        }
      } else {
        $scope.destRoom = $scope.roomList[0];
      }
    };

    $scope.changeId = function () {
      if (lmEditor.cacheValue(listKey, roomAreaId + ':' + newRoom.destId)) {
        $scope.hasError = true;
        $scope.lastError = "Room already exists";
        newRoom.destId = prevDestId;
      } else {
        $scope.hasError = false;
        prevDestId = newRoom.destId;
        $scope.lastError = null;
      }
    };

    $scope.changeArea = function () {
      loadArea($scope.destAreaId);
    };

    function loadArea() {
      lmEditor.deref(listKey);
      listKey = 'room:' + $scope.destAreaId;
      lmEditor.cache(listKey).then(function (rooms) {
        $scope.roomsInvalid = rooms.length === 0;
        $scope.hasError = $scope.roomsInvalid;
        if (rooms.length) {
          $scope.roomList = rooms;
        } else {
          $scope.roomList = [
            {title: "NO VALID ROOMS", dbo_id: "NO VALID ROOMS"}
          ];
        }
        $scope.changeType();
      })
    }

    $scope.digExit = function () {
      var destId = $scope.useNew ? $scope.destAreaId + ':' + $scope.destRoom.destId : $scope.destRoom.dbo_id;
      var newExit = {start_room: room.dbo_id, direction: $scope.direction.key, is_new: $scope.useNew,
        dest_id: destId, one_way: $scope.oneWay, dest_title: $scope.destRoom.title};
      lmRemote.request('editor/room/create_exit', newExit).then(function (newExit) {
        room.exits.push(newExit);
        roomController.addExit(newExit);
        lmEditor.deref(listKey);
        $scope.dismiss();
      }, function (error) {
        $scope.lastError = error.text;
      })
    }
  }
]);

angular.module('lampost_editor').controller('NewResetCtrl', ['$scope', 'addFunc', 'roomId', 'resetType', 'lmEditor', 'areaId',
  function ($scope, addFunc, roomId, resetType, lmEditor, areaId) {

    var invalidObject = {dbo_id: 'No ' + resetType + 's', title: 'No ' + resetType + 's', desc: ''};
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
    $scope.reset = {count: 1, max: 1, object: invalidObject, article_loads: []};

    $scope.changeArea = function () {
      lmEditor.loadObjects(resetType.toLowerCase(), $scope.areaId).then(function (objects) {
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
      angular.forEach(objects, function (object) {
        object.objectId = object.dbo_id.split(':')[1];
      });
      $scope.objects = objects;
      $scope.reset.object = objects[0];
    }

    $scope.createReset = function () {
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


    $scope.changeArea = function () {
      lmEditor.loadObjects('article', $scope.areaId).then(function (articles) {
        loadObjects(articles);
      });
    };

    $scope.changeArea();

    function loadObjects(articles) {
      if (articles.length == 0) {
        $scope.articles = [
          {dbo_id: "No articles in area"}
        ];
        $scope.addDisabled = true;
      } else {
        $scope.articles = articles;
        $scope.addDisabled = false;
      }
      $scope.newArticle = $scope.articles[0];
    }

    $scope.addArticleLoad = function () {
      var articleLoad = {article_id: $scope.newArticle.dbo_id, count: 1};
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

    $scope.deleteArticleLoad = function (articleIndex) {
      $scope.article_loads.splice(articleIndex, 1);
    };

    $scope.saveArticleLoads = function () {
      reset.article_loads = $scope.article_loads;
      updateFunc();
      $scope.dismiss();
    };


  }]);
