angular.module('lampost').controller('StatusTabCtrl', ['$scope', 'lmData', 'lmBus',
  function($scope, lmData, lmBus) {

    $scope.statsList = ['health', 'mental', 'stamina', 'action'];
    $scope.stats = {action: {label: 'Action'},
      health: {label: 'Health'},
      stamina:  {label: 'Stamina'},
      mental: {label: 'Mental'}};

    updateStatus(lmData.status);

    lmBus.register('status', updateStatus);

    function updateStatus(status) {

      $scope.status = status;
      angular.forEach($scope.statsList, function(key) {
        var stats = $scope.stats[key];
        var perc = Math.ceil(100 * status[key] / status['base_' + key]).toString();
        stats.style =  {width: perc.toString() + '%'};
        if (perc < 20) {
          stats.class = 'progress-danger';
        } else if (perc < 50) {
          stats.class = 'progress-warning';
        } else {
          stats.class = 'progress-success';
        }
      });
    }

  }]);
