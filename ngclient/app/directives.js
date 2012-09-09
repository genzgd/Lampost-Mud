angular.module('lampost_dir', []);

angular.module('lampost_dir').directive("enterKey", function() {
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {
            element.bind('keypress', function(event) {
                if (event.keyCode == 13) {
                    scope.$eval(attrs.enterKey);
                    event.preventDefault();
                    return false;
                }
                return true;
            })
        }
    }
});

angular.module('lampost_dir').directive('lmBlur', function() {
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {
            element.bind('blur', function() {
                scope.$eval(attrs.lmBlur);
            });
        }
    }

});

angular.module('lampost_dir').directive('scrollBottom', ['$timeout', function($timeout) {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            scope.$watch(attrs.scrollBottom, function() {
                $timeout(function () {
                    var scrollHeight = element[0].scrollHeight;
                    if (scrollHeight) {
                        element.scrollTop(scrollHeight);
                    }
                });
            })
        }
    };
}]);

angular.module('lampost_dir').directive('history', function() {
    return {
        restrict: 'A',
        link: function(scope, element) {
            element.bind('keydown', function(event) {
                var apply = null;
                if (event.keyCode == 38) {
                    apply = function() {scope.historyUp()};
                } else if (event.keyCode == 40) {
                    apply = function() {scope.historyDown()};
                }
                if (apply) {
                    scope.$apply(apply);
                    event.preventDefault();
                    return false;
                }
                return true;
            });
        }
    }
});

angular.module('lampost_dir').directive("prefFocus", ['$rootScope', '$timeout', function($rootScope, $timeout) {
    return {
        restrict: "A",
        link: function(scope, element) {
            scope.$on("refocus", forceFocus);
            var timer = $timeout(forceFocus);
            function forceFocus() {
                $timeout.cancel(timer);
                $(element)[0].focus();
            }
        }
    }
}]);

angular.module('lampost_dir').directive("altText", [function() {
    return {
        restrict: "A",
        link: function(scope, element, attrs) {
            element.attr("title", scope.$eval(attrs.altText));
        }
    }

}]);