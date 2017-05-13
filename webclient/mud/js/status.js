angular.module('lampost_mud').controller('StatusTabCtrl', ['$scope', 'lpData', 'lpEvent',
  function($scope, lpData, lpEvent) {

    $scope.statsList = ['health', 'mental', 'stamina', 'action'];
    $scope.stats = {action: {label: 'Action'},
      health: {label: 'Health'},
      stamina:  {label: 'Stamina'},
      mental: {label: 'Mental'}};
    $scope.oppStats = angular.copy($scope.stats);

    updateStatus(lpData.status);

    lpEvent.register('status', updateStatus, $scope);

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
          stats.class = 'progress-bar-danger';
        } else if (perc < 50) {
          stats.class = 'progress-bar-warning';
        } else {
          stats.class = 'progress-bar-success';
        }
      });
    }

  }]);
