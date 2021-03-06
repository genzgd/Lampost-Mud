angular.module('lampost_dir', []);

angular.module('lampost_dir').directive("enterKey", function () {
    return {
        restrict:'A',
        link:function (scope, element, attrs) {
            element.bind('keypress', function (event) {
                if (event.keyCode == 13) {
                    event.preventDefault();
                    scope.$apply(scope.$eval(attrs.enterKey));
                    return false;
                }
                return true;
            })
        }
    }
});

angular.module('lampost_dir').directive('autoComplete', function () {
    return {
        restrict:'A',
        require:'ngModel',
        link:function (scope, element, attrs, ngModel) {
            var opts = {};
            opts.source = scope.$eval(attrs.autoComplete);
            opts.updater = function (item) {
                ngModel.$setViewValue(item);
            };
            element.typeahead(opts);
        }
    }
});


angular.module('lampost_dir').directive('scrollBottom', ['$timeout', function ($timeout) {
    return {
        restrict:'A',
        link:function (scope, element, attrs) {
            scope.$watch(attrs.scrollBottom, function () {
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

angular.module('lampost_dir').directive('history', function () {
    return {
        restrict:'A',
        link:function (scope, element) {
            element.bind('keydown', function (event) {
                var apply = null;
                if (event.keyCode == 38) {
                    apply = function () {
                        scope.historyUp()
                    };
                } else if (event.keyCode == 40) {
                    apply = function () {
                        scope.historyDown()
                    };
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

angular.module('lampost_dir').directive("prefFocus", ['$rootScope', '$timeout', function ($rootScope, $timeout) {
    return {
        restrict:"A",
        link:function (scope, element) {
            scope.$on("refocus", forceFocus);
            var timer = $timeout(forceFocus);

            function forceFocus() {
                $timeout.cancel(timer);
                $(element)[0].focus();
            }
        }
    }
}]);

angular.module('lampost_dir').directive("lmStep", [function() {
  return {
    restrict: "A",
    link: function(scope, element, attrs) {
      element.attr("step", scope.$eval(attrs.lmStep));
    }
  }
}]);


angular.module('lampost_dir').directive("colorPicker", [function () {
    return {
        restrict: "A",
        scope: {color: '=ngModel'},
        link: function (scope, element) {
            element.spectrum({
                color: scope.color,
                change: function(color) {
                    scope.$apply(function() {
                        scope.color = color.toHexString(true);
                    });
                },
                showInitial: true,
                showInput: true,
                preferredFormat: 'hex'
            });
            scope.$watch('color', function() {
                element.spectrum('set', scope.color);
            });
        }
    }

}]);
