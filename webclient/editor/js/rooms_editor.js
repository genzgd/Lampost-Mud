angular.module('lampost_editor').controller('RoomEditorCtrl', ['$q', '$scope', 'lmRemote', 'lpEditor', 'lpCache', '$timeout', 'lmDialog',
  function ($q, $scope, lmRemote, lpEditor, lpCache, $timeout, lmDialog) {


    $scope.addTypes = [
      {id: 'exit', label: 'Exit'}
    ];

    $scope.setAddType = function (addType) {
      if (!$scope.activeAdd) {
        $scope.activeAdd = addType;
        $scope.addPanel = 'editor/panels/new_' + addType.id + '.html';
      }
    };

    $scope.closeAdd = function() {
      $scope.activeAdd = null;
      $scope.addPanel = null;
    };

    lpCache.cache('area').then(function (data) {
      $scope.areaList = data;
      $scope.areaNames = [];
      $scope.exitAreaNames = [];
      angular.forEach(data, function (area) {
        $scope.areaNames.push(area.dbo_id);
        if (area.can_write) {
          $scope.exitAreaNames.push(area.dbo_id)
        }
      });
    });

    $scope.directions = lpEditor.constants.directions;


    var self = this;
    var cacheKeys = [];

    function editFeature(feature, isAdd) {
      lmDialog.show({templateUrl: "editor/dialogs/edit-" + feature.sub_class_id + ".html", controller: feature.sub_class_id + "FeatureController",
        locals: {room: $scope.model, feature: feature, isAdd: isAdd}, noEscape: true});
    }

    this.addExit = function (exit) {
      originalModel().exits.push(exit);
      addRef('room', exit.destination);
    };

    this.newDialog = function (newModel) {
      newModel.id = $scope.selectedArea.next_room_id;
    };

    this.preCreate = function (newModel) {
      newModel.dbo_id = $scope.selectedAreaId + ":" + newModel.id;
    };

    $scope.availFeatures = {store: 'store', entrance: 'entrance'};


    $scope.exitTwoWay = function (exit) {
      var otherRoom = $scope.exitRoom(exit);
      if (!otherRoom) {
        return false; // This can happen temporarily while creating a new exit
      }
      var otherExits = otherRoom.exits;
      var rev_key = dirMap[exit.direction].rev_key;
      for (var i = 0; i < otherExits.length; i++) {
        var otherExit = otherExits[i];
        if (otherExit.direction === rev_key && otherExit.destination === $scope.model.dbo_id) {
          return true;
        }
      }
      return false;
    };


    $scope.deleteExit = function (exit, bothSides) {
      lmDialog.showConfirm("Delete Exit", "Are you sure you want to delete this exit", function () {
        lmRemote.request("editor/room/delete_exit",
          {start_room: $scope.model.dbo_id, both_sides: bothSides, dir: exit.direction}).then(function () {
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

    $scope.deleteExtra = function (extra) {
      if ($scope.currentExtra === extra) {
        $scope.currentExtra = null;
      }
      $scope.model.extras.splice($scope.model.extras.indexOf(extra), 1);
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

    $scope.addFeature = function () {
      var feature = angular.copy($scope.newFeature);
      if (feature.edit_required) {
        editFeature(feature, true)
      } else {
        $scope.model.features.push(feature);
      }
    };

    $scope.selectScript = function (script) {
      angular.forEach($scope.model.scripts, function (oldScript) {
        if (oldScript == script.dbo_id) {
          lmDialog.showOk("Script Exists", "This script is already in use.")
        }
      });
      $scope.model.scripts.push(script.dbo_id);
    };

    $scope.deleteScript = function (script_id) {
      $scope.model.scripts.splice($scope.model.scripts.indexOf(script_id), 1);
    };

    $scope.removeFeature = function (feature) {
      lmDialog.showConfirm("Remove Feature", "Are you sure you want to remove this feature?", function () {
        $scope.model.features.splice($scope.model.features.indexOf(feature), 1);
      });
    };

    $scope.editFeature = function (feature) {
      editFeature(feature);
    };

  }]);

angular.module('lampost_editor').controller('NewExitCtrl', ['$q', '$scope', 'lpEditor', 'lpCache', 'lmRemote',
  function ($q, $scope, lpEditor, lpCache, lmRemote) {

    var area;
    var listKey;
    var prevDestId;

    var roomAreaId = $scope.model.dbo_id.split(':')[0];
    var newRoom = {};

    $scope.hasError = false;
    $scope.lastError = null;
    $scope.oneWay = false;
    $scope.destAreaId = roomAreaId;
    $scope.useNew = true;
    $scope.direction = $scope.directions[0];

    $scope.changeType = function () {
      $scope.hasError = false;
      if ($scope.useNew) {
        $scope.destRoom = newRoom;
        if ($scope.destAreaId !== roomAreaId) {
          $scope.destAreaId = roomAreaId;
        }
      } else {
        $scope.destRoom = $scope.roomList[0];
      }
    };

    $scope.changeId = function () {
      if (lpCache.cacheValue(listKey, roomAreaId + ':' + newRoom.destId)) {
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
      lpCache.deref(listKey);
      listKey = 'room:' + $scope.destAreaId;
      lpCache.cache(listKey).then(function (rooms) {
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
      var newExit = {start_room: $scope.model.dbo_id, direction: $scope.direction.dbo_id, is_new: $scope.useNew,
        dest_id: destId, one_way: $scope.oneWay, dest_title: $scope.destRoom.title};
      lmRemote.request('editor/room/create_exit', newExit).then(function (newExit) {
        $scope.model.exits.push(newExit);
        lpEditor.original.push(newExit);
        $scope.closeAdd();
      }, function (error) {
        $scope.lastError = error.text;
      })
    };

    $scope.$on('$destroy', function () {
      lpCache.deref(listKey)
    });

    area = lpEditor.context.parent;
    newRoom.title = area.name + " Room " + area.next_room_id;
    newRoom.destId = area.next_room_id;
    prevDestId = newRoom.destId;

    $scope.changeArea();
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
