angular.module('lampost_editor').controller('AreaEditorCtrl', ['$scope', 'lmEditor', 'lmBus',
  function ($scope, lmEditor, lmBus) {

    lmEditor.prepare(this, $scope).prepareList('area');

    this.startEdit = function(area) {
      $scope.areaId = area.dbo_id;
      $scope.selectedAreaId = area.dbo_id;
      $scope.activateArea(area.dbo_id);
    };

    this.postDelete = function(area) {
      if (area == $scope.activeArea) {
        $scope.activateArea(null);
      }
    };

    lmBus.register('editorChange', function(currentEditor) {
      if (currentEditor === $scope.editor && $scope.model) {
        $scope.activateArea($scope.model.dbo_id);
      }
    })

  }]);


angular.module('lampost_editor').controller('RoomListCtrl', ['$q', '$scope', 'lmEditor',
  function ($q, $scope, lmEditor) {

    var listKey;

    $scope.editor = {id: 'room', url: "room", create: 'dialog', label: 'Room'};

    var refresh = lmEditor.prepare(this, $scope).prepareList;

    $scope.$on('updateModel', function () {
      if ($scope.model) {
        lmEditor.deref(listKey);
        listKey = "room:" + $scope.areaId;
        refresh(listKey);
      } else {
        $scope.modelList = null;
      }
    });

    this.newDialog = function (newModel) {
      newModel.id = $scope.model.next_room_id;
    };

    this.preCreate = function (newModel) {
      newModel.dbo_id = $scope.areaId + ":" + newModel.id;
    };

    this.postCreate = function (newModel) {
      $scope.startEditor('room', newModel);
      return $q.reject();
    };

  }]);


angular.module('lampost_editor').controller('MobileListCtrl', ['$q', '$scope', 'lmEditor',
  function ($q, $scope, lmEditor, lmEditorMobile) {

    var listKey;

    $scope.editor = {id: 'mobile', url: "mobile", create: 'dialog', label: 'Mobile'};
    var helpers = lmEditor.prepare(this, $scope);

    $scope.$on('updateModel', function () {
      if ($scope.model) {
        lmEditor.deref(listKey);
        listKey = "mobile:" + $scope.areaId;
        helpers.prepareList(listKey);
      } else {
        $scope.modelList = null;
      }
    });

    this.newDialog = function (newModel) {
      newModel.level = 1;
    };

    this.preCreate = function (newModel) {
      newModel.dbo_id = $scope.areaId + ":" + newModel.id;
    };

    this.postCreate = function (newModel) {
      $scope.startEditor('mobile', newModel);
      return $q.reject();
    };

  }]);

angular.module('lampost_editor').controller('MobileEditorCtrl', ['$q', '$scope', 'lmEditor',
  function ($q, $scope, lmEditor) {

    var helpers = lmEditor.prepare(this, $scope);

    $scope.defaultSkills = {effectDesc: "Default skills and levels assigned to this mobile", effectName: "Default Skills",
      attrWatch: "default_skills"};

    this.newDialog = function (newModel) {
      newModel.level = 1;
    };

    this.delConfirm = function (delModel) {
      lmEditorMobile.delete(delModel, helpers.mainDelete);
      return $q.reject();
    };

    this.delConfirm = function (delModel) {
      lmEditorMobile.delete(delModel, helpers.mainDelete);
      return $q.reject();
    };

    this.preCreate = function (newModel) {
      newModel.dbo_id = $scope.selectedAreaId + ":" + newModel.id;
    };

    $scope.editor.newEdit($scope.editor.editModel);
  }]);


angular.module('lampost_editor').controller('ArticleListCtrl', ['$q', '$scope', 'lmEditor',
  function ($q, $scope, lmEditor) {

    var listKey;

    $scope.editor = {id: 'article', url: "article", create: 'dialog', label: 'Article'};
    var helpers = lmEditor.prepare(this, $scope);

    $scope.$on('updateModel', function () {
      if ($scope.model) {
        lmEditor.deref(listKey);
        listKey = "article:" + $scope.areaId;
        helpers.prepareList(listKey);
      } else {
        $scope.modelList = null;
      }
    });

    this.newDialog = function (newModel) {
      newModel.level = 1;
      newModel.weight = 1;
    };

    this.preCreate = function (newModel) {
      newModel.dbo_id = $scope.areaId + ":" + newModel.id;
      newModel.equip_slot = 'none';
    };

    this.delConfirm = function (delModel) {
      lmEditorArticle.delete(delModel, helpers.mainDelete);
      return $q.reject();
    };

    this.postCreate = function (newModel) {
      $scope.startEditor('article', newModel);
      return $q.reject();
    };

  }]);


angular.module('lampost_editor').controller('ArticleEditorCtrl', ['$q', '$scope', 'lmEditor',
  function ($q, $scope, lmEditor) {

    lmEditor.prepare(this, $scope);

    this.newDialog = function (newModel) {
      newModel.level = 1;
      newModel.weight = 1;
    };

    this.preCreate = function (article) {
      article.dbo_id = $scope.selectedAreaId + ":" + article.id;
      if (article.equip_slot == 'none') {
        article.equip_slot = null;
      }
    };

    this.preUpdate = function(article) {
      if (article.equip_slot == 'none') {
        article.equip_slot = null;
      }
    };

    this.postUpdate = function(article) {
       if (!article.equip_slot) {
        article.equip_slot = 'none';
      }
    };

    this.startEdit = function(article) {
      if (!article.equip_slot) {
        article.equip_slot = 'none';
      }
    };

    $scope.editor.newEdit($scope.editor.editModel);
  }]);
