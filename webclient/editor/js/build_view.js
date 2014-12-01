angular.module('lampost_editor').service('lpBuildService', ['lpEvent', 'lpEditor', function (lpEvent, lpEditor) {

  lpEditor.registerContext('area', {
    extend: function (model) {
      model.next_room_id = 1;
    }
  });

  lpEditor.registerContext('room', {
    parentType: 'area',
    extend: function (model) {
      angular.extend(model, {dbo_id: this.parent.next_room_id, exits: [], mobile_resets: [],
        article_resets: [], extras: [], features: []});
    },
    refs: [
      {type: 'room', path: 'exits.destination'}
    ]
  });

  lpEditor.registerContext('mobile', {
    parentType: 'area',
    extend: function(model) {
      model.level = 1;
      model.affinity = 'neutral';
    }
  })

}]);

angular.module('lampost_editor').controller('BuildViewCtrl', ['$scope', 'lpEvent', 'lpBuildService', 'lpEditor',
  function ($scope, lpEvent, lpBuildService, lpEditor) {

    var editArea = null;

    $scope.activeArea = function () {
      return editArea ? editArea.name : '-NOT SET-';
    };


    $scope.newEditor = function (editorId, event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      lpEvent.dispatch('newEdit', editorId);
    }


  }]);