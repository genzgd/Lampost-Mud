angular.module('lampost_editor').controller('RoomEditorCtrl', ['$q', '$scope', 'lmRemote', 'lmEditor', '$timeout', 'lmDialog',
  function ($q, $scope, lmRemote, lmEditor, $timeout, lmDialog) {

    var self = this;
    var cacheKeys = [];
    var dirMap = {};
    var originalModel = lmEditor.prepare(this, $scope).originalModel;

    function addRef(childType, childId) {
      var childKey = childType + ':' + childId.split(":")[0];
      if (cacheKeys.indexOf(childKey) == -1) {
        cacheKeys.push(childKey);
        return lmEditor.cache(childKey);
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
        editPromises.push(addRef('room', exit.destination));
      });
      angular.forEach(room.mobile_resets, function (reset) {
        editPromises.push(addRef('mobile', reset.mobile_id));
        angular.forEach(reset.article_loads, function (article_load) {
          editPromises.push(addRef('article', article_load.article_id));
        })
      });
      angular.forEach(room.article_resets, function (reset) {
        editPromises.push(addRef('article', reset.article_id));
      });
      return $q.all(editPromises);
    };

    this.postDelete = function () {
      $scope.startEditor('area');
    };

    $scope.editor.newEdit($scope.editor.editModel);

    this.addExit = function (exit) {
      originalModel().exits.push(exit);
      addRef('room', exit.destination);
    };

    $scope.visitRoom = function () {
      lmEditor.visitRoom($scope.model.dbo_id);
    };

    $scope.exitRoom = function (exit) {
      return lmEditor.cacheValue('room:' + exit.destination.split(':')[0], exit.destination);
    };

    $scope.resetMobile = function (mobileReset) {
      return lmEditor.cacheValue('mobile:' + mobileReset.mobile_id.split(':')[0], mobileReset.mobile_id);
    };

    $scope.resetArticle = function (articleReset) {
      return lmEditor.cacheValue('article:' + articleReset.article_id.split(':')[0], articleReset.article_id);
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

    $scope.addNewReset = function (resetType) {
      lmDialog.show({templateUrl: "editor/dialogs/new_reset.html", controller: "NewResetCtrl", scope: $scope.$new(),
        locals: {room: $scope.model, resetType: resetType}});
    };

    $scope.deleteMobile = function (mobileIx) {
      $scope.model.mobile_resets.splice(mobileIx);
    };

    $scope.mobileArticles = function (mobileReset, mobile) {
      var scope = $scope.$new();
      scope.mobileTitle = mobile.title;
      lmDialog.show({templateUrl: "editor/dialogs/article_load.html", controller: "ArticleLoadCtrl",
        scope: scope, locals: {reset: mobileReset, areaId: $scope.model.dbo_id.split(':')[0]}});
    };

    $scope.deleteArticle = function (articleIx) {
      $scope.model.article_resets.splice(articleIx);
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
    };

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
    };

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
      })]).then($scope.changeArea);

  }]);

angular.module('lampost_editor').controller('NewResetCtrl', ['$scope', 'lmEditor', 'room', 'resetType',
  function ($scope, lmEditor, room, resetType) {

    var listKey;
    var resetLabel = resetType.substring(0, 1).toUpperCase() + resetType.substring(1);
    var invalidObject = {dbo_id: ':No ' + resetLabel + 's', title: 'No ' + resetLabel + 's', desc: ''};
    $scope.resetLabel = resetLabel;
    $scope.disabled = true;
    $scope.room = room;
    lmEditor.cache('area').then(function (areas) {
      $scope.areaList = areas;
      $scope.areaId = room.dbo_id.split(':')[0];
      $scope.changeArea();
    });
    $scope.reset = {reset_count: 1, reset_max: 1, object: invalidObject, article_loads: []};

    $scope.changeArea = function () {
      lmEditor.deref(listKey);
      listKey = resetType + ':' + $scope.areaId;
      lmEditor.cache(listKey).then(function (objects) {
        $scope.disabled = objects.length == 0;
        if ($scope.disabled) {
          objects = [invalidObject];
        }
        $scope.objects = objects;
        $scope.reset.object = objects[0];
      });
    };

    $scope.createReset = function () {
      lmEditor.deref(listKey);
      $scope.reset[resetType + "_id"] = $scope.reset.object.dbo_id;
      delete $scope.object;
      room[resetType + "_resets"].push($scope.reset);
      $scope.dismiss();
    };

  }]);

angular.module('lampost_editor').controller('ArticleLoadCtrl', ['$scope', 'lmEditor', 'reset', 'areaId',
  function ($scope, lmEditor, reset, areaId) {

    var listKey;
    var invalidObject = {dbo_id: 'No articles', title: 'No articles', desc: ''};
    $scope.newArticle = {};
    $scope.disabled = true;
    $scope.article_loads = angular.copy(reset.article_loads);
    $scope.areaId = areaId;

    lmEditor.cache("constants").then(function (constants) {
      $scope.article_load_types = constants.article_load_types;
      lmEditor.cache('area').then(function (areas) {
        $scope.areaList = areas;
        $scope.changeArea();
      });
    });

    $scope.changeArea = function () {
      lmEditor.deref(listKey);
      listKey = 'article:' + $scope.areaId;
      lmEditor.cache(listKey).then(function (articles) {
        $scope.disabled = articles.length == 0;
        if ($scope.disabled) {
          articles = [invalidObject];
        }
        $scope.articles = articles;
        $scope.newArticle = articles[0];
      });
    };

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
      $scope.dismiss();
    };


  }]);
