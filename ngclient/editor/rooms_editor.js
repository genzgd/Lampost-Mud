angular.module('lampost_editor').controller('RoomEditorCtrl', ['$scope', 'lmBus', 'lmRemote', 'lmEditor', '$timeout', 'lmDialog',
  function ($scope, lmBus, lmRemote, lmEditor, $timeout, lmDialog) {

    var areaId = null;

    this.startEdit = function (model) {
      areaId = model.dbo_id.split(':')[0];
    };

    lmEditor.cacheEntry('area');
    lmEditor.prepare(this, $scope);
    $scope.editor.newEdit($scope.editor.editModel);

    function showResult(type, message) {
      $scope.showResult = true;
      $scope.resultMessage = message;
      $scope.resultType = 'alert-' + type;
    }

    $scope.visitRoom = function () {
      lmEditor.visitRoom($scope.model.dbo_id);
    };

    $scope.addNewExit = function () {
      lmDialog.show({templateUrl: "editor/dialogs/new_exit.html", controller: "NewExitCtrl",
        locals: {parentScope: $scope, room: $scope.model}});
    };

    $scope.deleteExit = function (exit, bothSides) {
      var exitData = {start_room: $scope.roomId, both_sides: bothSides, dir: exit.dir};
      lmRemote.request($scope.editor.url + "/delete_exit", exitData).then(function (result) {
          lmEditor.exitDeleted(result.exit);
          result.other_exit && lmEditor.exitDeleted(result.other_exit);
          result.room_deleted && lmEditor.roomDeleted(result.room_deleted);
        }
      )
    };

    $scope.addNewExtra = function () {
      var newExtra = {title: "", desc: "", aliases: ""};
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

    $scope.addNewMobile = function () {
      lmDialog.show({templateUrl: "editor/dialogs/new_reset.html", controller: "NewResetCtrl",
        locals: {addFunc: addMobileReset, roomId: $scope.roomId, resetType: 'Mobile', areaId: areaId}});
    };

    $scope.deleteMobile = function (mobileIx) {
      $scope.roomDirty = true;
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
      $scope.roomDirty = true;
      $scope.room.articles.splice(articleIx);
    };

    $scope.showDesc = function (extra) {
      $scope.currentExtra = extra;
      $scope.extraDisplay = 'desc';
    };

    $scope.newAlias = function () {
      $scope.currentExtra.editAliases.push({title: ""});
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
        angular.forEach($scope.room.exits.slice(), function (value, index) {
          if (value.dir == exit.dir) {
            $scope.room.exits.splice(index, 1);
          }
        })
      }
    }

    function roomUpdated(room) {
      angular.forEach($scope.room.exits, function (exit) {
        if (exit.dest_id == room.id) {
          exit.dest_title = room.title;
          exit.dest_desc = room.desc;
        }
      });
    }

    function mobileUpdated(newmobile) {
      angular.forEach($scope.room.mobiles, function (mobile) {
        if (mobile.dbo.id == newmobile.dbo_id) {
          mobile.title = newmobile.title;
          mobile.desc = newmobile.desc;
        }
      });
    }

    function mobileDeleted(mobileId) {
      angular.forEach($scope.room.mobiles.slice(), function (mobile) {
        if (mobile.dbo.id = mobileId) {
          $scope.room.mobiles.splice($scope.room.mobiles.indexOf(mobile), 1);
        }
      });
      angular.forEach(roomCopy.mobiles.slice(), function (mobile) {
        if (mobile.dbo.id = mobileId) {
          roomCopy.mobiles.splice(roomCopy.mobiles.indexOf(mobile), 1);
        }
      });
    }

    function articleUpdated(newarticle) {
      angular.forEach($scope.room.articles, function (article) {
        if (article.dbo_id == newarticle.dbo_id) {
          article.title = newarticle.title;
          article.desc = newarticle.desc;
        }
      });
    }

    function articleDeleted(articleId) {
      angular.forEach($scope.room.articles.slice(), function (article) {
        if (article.dbo_id = articleId) {
          $scope.room.articles.splice($scope.room.articles.indexOf(article), 1);
        }
      });
      angular.forEach(roomCopy.articles.slice(), function (article) {
        if (article.dbo_id = articleId) {
          roomCopy.articles.splice(roomCopy.articles.indexOf(article), 1);
        }
      });
    }

    function updateExtras() {
      if ($scope.currentExtra && !$scope.currentExtra.title) {
        $scope.currentExtra = null;
      }
      angular.forEach($scope.room.extras, function (extra) {
        if (extra.hasOwnProperty('editAliases')) {
          extra.aliases = [];
          angular.forEach(extra.editAliases, function (editAlias) {
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
          editAliases.push({title: extra.aliases[i]});
        }
        extra.editAliases = editAliases;
      }
      $scope.currentExtra = extra;
      $scope.extraDisplay = 'aliases';
    };


    function addMobileReset(reset) {
      var newReset = {mobile_id: reset.object.dbo_id, mob_count: reset.count, mob_max: reset.max,
        title: reset.object.title, desc: reset.object.desc};
      $scope.room.mobiles.push(newReset);
      $scope.dirty();
    }

    function addArticleReset(reset) {
      var newReset = {article_id: reset.object.dbo_id, article_count: reset.count, article_max: reset.max,
        title: reset.object.title, desc: reset.object.desc};
      $scope.room.articles.push(newReset);
      $scope.dirty();
    }

    function updateArticleLoads() {
      $scope.dirty();
    }

  }]);

angular.module('lampost_editor').controller('NewExitCtrl', ['$q', '$scope', 'lmEditor', 'lmRemote', 'room',
  function ($q, $scope, lmEditor, lmRemote, room) {

    var area;
    var listKey;
    var prevDestId;

    var roomAreaId = room.dbo_id.split(':')[0];
    var newRoom = {};

    $scope.titleEdited = false;
    $scope.hasError = false;
    $scope.lastError = null;
    $scope.oneWay = false;
    $scope.destAreaId = roomAreaId;

    $q.all([
      lmEditor.cache('constants').then(function (constants) {
        $scope.directions = constants.directions;
        $scope.direction = $scope.directions[0];
      }),
      lmEditor.cache('area').then(function (areas, areaMap) {
        $scope.areaList = areas;
        area = lmEditor.cacheValue('area', roomAreaId);
        newRoom.title = area.name + " Room " + area.next_room_id;
        newRoom.destId = area.next_room_id;
        prevDestId = newRoom.destId;
      })]).then(loadArea);

    $scope.useNew = true;

    $scope.changeType = function () {
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
        prevDestId = newRoom.destId;
        $scope.lastError = null;
        $scope.hasError = false;
      }
    };

    $scope.changeArea = function () {
      loadArea($scope.destAreaId);
    };

    function loadArea() {
      lmEditor.deref(listKey);
      listKey = 'room:' + $scope.destAreaId;
      lmEditor.cacheEntry({key: listKey, url: 'room/list/' + $scope.destAreaId, idSort: true});
      lmEditor.cache(listKey).then(function (rooms) {
         $scope.roomsInvalid = rooms.length === 0;
         $scope.hasError = $scope.roomsInvalid;
        if (rooms.length) {
          $scope.roomList = rooms;
        } else {
          $scope.roomList = [{title: "NO VALID ROOMS", dbo_id:"NO VALID ROOMS"}];
        }
        $scope.changeType();
      })
    }

    $scope.digExit = function () {
      var newExit = {start_room: roomId, direction: $scope.direction.key, is_new: $scope.useNew == 'new',
        dest_area: $scope.destAreaId, dest_id: $scope.destId, one_way: $scope.oneWay,
        dest_title: $scope.destTitle};
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
