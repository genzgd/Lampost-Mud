angular.module('lampost').controller('StatusTabCtrl', ['$scope', 'lmData', 'lmBus',
  function($scope, lmData, lmBus) {

    $scope.statsList = ['health', 'mental', 'stamina', 'action'];
    $scope.stats = {action: {label: 'Action'},
      health: {label: 'Health'},
      stamina:  {label: 'Stamina'},
      mental: {label: 'Mental'}};
    $scope.oppStats = angular.copy($scope.stats);

    updateStatus(lmData.status);

    lmBus.register('status', updateStatus);

    function updateStatus(status) {
      $scope.status = status;
      updateBars($scope.stats, status);
      $scope.opponent = status.opponent;
      if ($scope.opponent) {
        updateBars($scope.oppStats, $scope.opponent);
      }
    }

    function updateBars(barStats, rawStats) {
       angular.forEach($scope.statsList, function(key) {
        var stats = barStats[key];
        var perc = Math.ceil(100 * rawStats[key] / rawStats['base_' + key]).toString();
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
