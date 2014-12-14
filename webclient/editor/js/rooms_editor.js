angular.module('lampost_editor').controller('RoomEditorCtrl',
 ['$q', '$scope', '$timeout', 'lpRemote', 'lpEvent', 'lpEditor', 'lpCache', '$timeout', 'lpDialog', 'lpEditorView',
  function ($q, $scope, $timeout, lpRemote, lpEvent, lpEditor, lpCache, $timeout, lpDialog, lpEditorView) {

    var mobileOptions = {addLabel: 'Mobile', addId: 'mobile', resetType: 'mobile', resetInclude: null};
    var articleOptions = {addLabel: 'Article', addId: 'article', resetType: 'article',
     resetInclude: 'editor/panels/article_load.html'};
    var wideMode = {'store': true};

    $scope.dirMap = {};

    $scope.addTypes = [
      {id: 'new_exit', label: 'Exit'},
      {id: 'room_reset', label: 'Mobile', options: mobileOptions},
      {id: 'room_reset', label: 'Article', options: articleOptions},
      {id: 'extra', label: 'Extra'},
      {id: 'feature', label: 'Feature'}
    ];

    $scope.setAddType = function (addType, addOptions, addObj) {
      lpEditor.addOpts = addOptions;
      lpEditor.addObj = addObj;

      $scope.activeAdd = addType;
      $scope.wideMode = wideMode[addType];
      $scope.addPanel = 'editor/panels/' + addType + '.html';
      $scope.$broadcast('addInit');
    };

    $scope.closeAdd = function () {
      $scope.activeAdd = null;
      $scope.addPanel = null;
      $scope.activeExit = null;
      $scope.newFeature = null;
      $scope.wideMode = false;
    };

    function loadAreas() {
      lpCache.cache('area').then(function (data) {
        $scope.areaList = data;
        $scope.exitAreas = [];
        angular.forEach(data, function (area) {
          if (area.can_write && area.room_list.length) {
            $scope.exitAreas.push(area)
          }
        });
      });
    }

    lpEvent.register('childListUpdated', loadAreas, $scope);

    loadAreas();

    $scope.directions = lpEditor.constants.directions;
    angular.forEach($scope.directions, function (dir) {
      $scope.dirMap[dir.dbo_id] = dir;
    });

    $scope.visit = function() {
      lpEditorView.mudWindow();
      lpRemote.request('editor/room/visit', {room_id: $scope.model.dbo_id});
    };

    $scope.exitRoom = function (exit) {
      return lpCache.cacheValue('room:' + exit.destination.split(':')[0], exit.destination);
    };

    $scope.exitTwoWay = function (exit) {
      var otherRoom = $scope.exitRoom(exit);
      if (!otherRoom) {
        return false; // This can happen temporarily while creating a new exit
      }
      var otherExits = otherRoom.exits;
      var rev_key = $scope.dirMap[exit.direction].rev_key;
      for (var i = 0; i < otherExits.length; i++) {
        var otherExit = otherExits[i];
        if (otherExit.direction === rev_key && otherExit.destination === $scope.model.dbo_id) {
          return true;
        }
      }
      return false;
    };

    $scope.modifyExit = function (exit) {
      $scope.activeExit = exit;
      $scope.setAddType('modify_exit');
    };

    $scope.resetCount = function(reset) {
      var count = '[' + reset.reset_count;
      if (reset.reset_count < reset.reset_max) {
        count += '-' + reset.reset_max;
      }
      count += ']';
      return count;
    };

    $scope.resetMobile = function (mobileReset) {
      return lpCache.cacheValue('mobile:' + mobileReset.mobile.split(':')[0], mobileReset.mobile);
    };

    $scope.modifyMobile = function(mobileReset) {
      $scope.closeAdd();
      $scope.setAddType('room_reset', mobileOptions, mobileReset);
    };

    $scope.resetArticle = function (mobileReset) {
      return lpCache.cacheValue('article:' + mobileReset.article.split(':')[0], mobileReset.article);
    };

    $scope.modifyArticle = function(articleReset) {
      $scope.closeAdd();
      $scope.setAddType('room_reset', articleOptions, articleReset);
    };

    $scope.modifyExtra = function(extra) {
      $scope.closeAdd();
      $scope.setAddType('extra', {}, extra);
    }

    function editFeature(feature, isAdd) {
      $scope.closeAdd();
      $scope.activeFeature = feature;
      $scope.setAddType(feature.sub_class_id, null, isAdd ? feature : undefined);
    }

    $scope.deleteExit = function (exit) {
      lpDialog.showConfirm("Delete Exit", "Are you sure you want to delete this exit", function () {
        lpRemote.request("editor/room/delete_exit",
          {start_room: $scope.model.dbo_id, both_sides: true, dir: exit.direction}).then(function () {
            $scope.closeAdd();

            var exitLoc = $scope.model.exits.indexOf(exit);
            if (exitLoc > -1) {
              $scope.model.exits.splice(exitLoc, 1);
            }
            var originalExits = lpEditor.original.exits;
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


    $scope.startFeature = function (newFeature) {
      $scope.closeAdd();
      var feature = angular.copy(newFeature);
      if (feature.edit_required) {
        editFeature(feature, true)
      } else {
        $scope.model.features.push(feature);
      }
    };

    $scope.deleteFeature = function () {
      $scope.model.features.splice($scope.model.features.indexOf($scope.activeFeature), 1);
      $scope.closeAdd();
    };

    $scope.selectScript = function (script) {
      angular.forEach($scope.model.scripts, function (oldScript) {
        if (oldScript == script.dbo_id) {
          lpDialog.showOk("Script Exists", "This script is already in use.")
        }
      });
      $scope.model.scripts.push(script.dbo_id);
    };

    $scope.deleteScript = function (script_id) {
      $scope.model.scripts.splice($scope.model.scripts.indexOf(script_id), 1);
    };

    $scope.modifyFeature = function (feature) {
      editFeature(feature);
    };

    lpEvent.register('editStarting', $scope.closeAdd, $scope);


  }]);


angular.module('lampost_editor').controller('RoomExtraCtrl', ['$scope', 'lpEditor', function($scope, lpEditor) {

  $scope.parentModel = $scope.model;

  function initialize() {
    if (lpEditor.addObj) {
      $scope.model = lpEditor.addObj;
      $scope.newAdd = false;
    } else {
      $scope.model = {desc: '', aliases: [], title: ''}
      $scope.newAdd = true;
    }
  }

  $scope.addNewAlias = function () {
    $scope.model.aliases.push('');
    $timeout(function () {
      jQuery('.alias-row:last').focus();
    });
  };


  $scope.deleteAlias = function (index) {
    $scope.model.aliases.splice(index, 1);
  };


  $scope.closeAdd = function() {
    if ($scope.newAdd || ($scope.model.title && $scope.model.desc)) {
      $scope.$parent.closeAdd();
    } else {
      $scope.lastError = "Title and Description required.";
    }
  }

  $scope.deleteExtra = function (extra) {
    $scope.parentModel.extras.splice($scope.parentModel.extras.indexOf($scope.model), 1);
    $scope.closeAdd();
  };

  $scope.createExtra = function () {
    $scope.parentModel.extras.push($scope.model);
    $scope.closeAdd();
  };

  $scope.$on('addInit', initialize);

  initialize();

}]);


angular.module('lampost_editor').controller('NewExitCtrl', ['$q', '$scope', 'lpEditor', 'lpCache', 'lpRemote',
  function ($q, $scope, lpEditor, lpCache, lpRemote) {

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
        $scope.roomList = rooms;
        $scope.changeType();
      })
    };

    $scope.digExit = function () {
      var destId = $scope.useNew ? $scope.destAreaId + ':' + $scope.destRoom.destId : $scope.destRoom.dbo_id;
      var newExit = {start_room: $scope.model.dbo_id, direction: $scope.direction.dbo_id, is_new: $scope.useNew,
        dest_id: destId, one_way: $scope.oneWay, dest_title: $scope.destRoom.title};
      lpRemote.request('editor/room/create_exit', newExit).then(function (newExit) {
        $scope.model.exits.push(newExit);
        lpEditor.original.exits.push(newExit);
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


angular.module('lampost_editor').controller('RoomResetCtrl', ['$scope', 'lpEvent', 'lpEditor', 'lpCache', 'lpUtil',
  function ($scope, lpEvent, lpEditor, lpCache, lpUtil) {

    var listKey;
    var origAreaId;
    var origResetId;

    function initialize() {
      angular.extend($scope, lpEditor.addOpts);
      $scope.vars = {};
      if (lpEditor.addObj) {
        $scope.newAdd = false;
        $scope.reset = lpEditor.addObj;
        origAreaId = $scope.reset[$scope.addId].split(':')[0];
        origResetId = $scope.reset[$scope.addId];
        $scope.vars.areaId = origAreaId;
      } else {
        $scope.newAdd = true;
        $scope.reset = {reset_key: 0, reset_ref: 0, reset_count: 1, reset_max: 1};
        $scope.vars.areaId = $scope.model.dbo_id.split(':')[0];;
      }

      findAreas();
      $scope.changeArea();
    }

    function findAreas() {
      $scope.sourceAreas = [];
      angular.forEach($scope.areaList, function(area) {
        var resetList = area[$scope.resetType + "_list"];
        if (resetList.length) {
          $scope.sourceAreas.push(area);
        } else if (area.dbo_id === $scope.vars.areaId) {
          $scope.vars.areaId = null;
        }
      });
      if ($scope.sourceAreas.length === 0) {
        $scope.validReset = false;
      } else {
        $scope.validReset = true;
        if (!$scope.vars.areaId) {
          $scope.vars.areaId = $scope.sourceAreas[0].dbo_id;
        }
      }
    }

    function loadResetObj() {
       $scope.resetObj = lpCache.cacheValue(listKey, $scope.reset[$scope.addId]);
    }

    $scope.changeArea = function () {
      if ($scope.validReset) {
        lpCache.deref(listKey);
        listKey = $scope.resetType + ':' + $scope.vars.areaId;
        lpCache.cache(listKey).then(function (objects) {
          $scope.objects = objects;
          if (origAreaId === $scope.vars.areaId) {
            $scope.reset[$scope.addId] = origResetId;
          } else {
            $scope.reset[$scope.addId] = objects[0].dbo_id;
          }
          loadResetObj();
        });
      }
    };

    $scope.changeResetId = function () {
      origAreaId = $scope.vars.areaId;
      origResetId = $scope.reset[$scope.addId];
      loadResetObj();
    };

    $scope.createReset = function () {
      var resets = $scope.model[$scope.resetType + "_resets"];
      lpUtil.intSort(resets, 'reset_key')
      if ($scope.resetType === 'mobile') {
        $scope.reset.reset_key = resets.length + 1;
        for (var ix = 0; ix < resets.length; ix++) {
          if (resets[ix].reset_key != ix + 1) {
            $scope.reset.reset_key = ix + 1;
            break;
          }
        }
      }
      resets.push($scope.reset);
      $scope.closeAdd();
    };

    $scope.deleteReset = function() {
      var resets = $scope.model[$scope.resetType + '_resets'];
      resets.splice(resets.indexOf($scope.reset), 1);
      $scope.closeAdd();
    };

    $scope.$on('$destroy', function() {
      lpCache.deref(listKey);
    });

    $scope.$on('addInit', initialize);

    lpEvent.register("modelDeleted", findAreas, $scope);
    lpEvent.register("modelUpdated", findAreas, $scope);
    lpEvent.register("modelInserted", findAreas, $scope);

    initialize();

  }]);

angular.module('lampost_editor').controller('ArticleLoadCtrl', ['$scope', 'lpUtil',
  function ($scope, lpUtil) {

    var roomReset = {reset_key: 0, mobile: '-ROOM-'};

    function initialize() {
      $scope.isEquip = $scope.reset.mobile_ref > 0 && $scope.reset.load_type === 'equip';
      $scope.mobileList = angular.copy($scope.model.mobile_resets);
      $scope.mobileList.unshift(roomReset);
    }

    $scope.changeEquip = function() {
      $scope.reset.load_type = $scope.isEquip ? 'equip' : 'inven';
    };

    $scope.changeMobileRef = function() {
      if ($scope.reset.mobile_ref == 0) {
        $scope.reset.load_type = 'equip';
        $scope.isEquip = true;
      }
    };

    $scope.$on('addInit', initialize);

    initialize();

  }]);
