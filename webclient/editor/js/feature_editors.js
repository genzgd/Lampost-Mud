angular.module('lampost_editor').controller('EditStoreCtrl', ['$scope', '$filter', function($scope, $filter) {

  var noCurrency = {dbo_id: ':--None--'};
  var noItems = {dbo_id: '--No Items--', invalid: true};

  $scope.store = $scope.activeFeature;
  $scope.currencyParent = $scope.store.currency ? $scope.store.currency.split(":")[0] : undefined;
  $scope.newPerm = {};

  $scope.setCurrencyList = function(objects) {
    $scope.currencyList = $filter('filter')(objects, {divisible: true});
    $scope.currencyList.unshift(noCurrency);

    for (var ix = 0; ix < $scope.currencyList.length; ix++) {
      if ($scope.store.currency == $scope.currencyList[ix].dbo_id) {
        $scope.newCurrency = $scope.store.currency;
        return;
      }
    }
    $scope.newCurrency = noCurrency.dbo_id;
    $scope.store.currency = null;
  };


  $scope.setPermList = function (objects) {
    $scope.permList = $filter('filter')(objects, {divisible: false});
    if ($scope.permList.length === 0) {
      $scope.permList = [noItems];
    }
    $scope.newPerm = $scope.permList[0].dbo_id;
  }

  $scope.updateCurrency = function() {
    if ($scope.newCurrency == noCurrency.dbo_id) {
      $scope.store.currency = null;
    } else {
      $scope.store.currency = $scope.newCurrency;
    }
  };

  $scope.addPerm = function() {
    $scope.store.perm_inven.push($scope.newPerm);
  };

  $scope.permExists = function() {
    return $scope.newPerm.invalid || $scope.store.perm_inven.indexOf($scope.newPerm) > -1;
  };

  $scope.removePerm = function(perm) {
    var ix = $scope.store.perm_inven.indexOf(perm);
    if (ix > -1) {
      $scope.store.perm_inven.splice(ix, 1);
    }
  };

}]);


angular.module('lampost_editor').controller('entranceFeatureController', ['$scope', '$filter', 'lmEditor', 'lpDialog',  'room', 'feature', 'isAdd',
  function($scope, $filter, lmEditor, lpDialog, room, feature, isAdd) {

    $scope.objType = 'room';
    $scope.entrance = angular.copy(feature);
    $scope.room = room;

    $scope.listChange = function(rooms) {

      if (rooms.length > 0) {
        $scope.roomList = rooms;
        $scope.hasRoom = true;
      } else {
        $scope.roomList = [{dbo_id: "N/A"}];
        $scope.hasRoom= false;
      }
       $scope.entranceRoom = $scope.roomList[0];
    };

    lmEditor.cache('constants').then(function (constants) {
        $scope.directions = constants.directions;
    });

    $scope.checkVerb = function() {
      if ($scope.entrance.verb) {
        $scope.entrance.direction = null;
      }
    };

    $scope.checkDirection = function () {
      if ($scope.entrance.direction) {
        $scope.entrance.verb = null;
      }
    };

    $scope.changeDest = function() {
      $scope.entrance.destination = $scope.entranceRoom.dbo_id;
    };

    $scope.finishEdit = function() {
      if (!$scope.entrance.destination) {
        lpDialog.showOk("Destination Request", "Please set a destination");
        return;
      }

      if (isAdd) {
        room.features.push($scope.entrance);
      } else {
        angular.copy($scope.entrance, feature);
      }
      $scope.dismiss();
    };

}]);
