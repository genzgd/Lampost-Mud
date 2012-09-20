angular.module('lampost_dir', []);

angular.module('lampost_dir').directive("enterKey", function () {
    return {
        restrict:'A',
        link:function (scope, element, attrs) {
            element.bind('keypress', function (event) {
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

angular.module('lampost_dir').directive('lmBlur', function () {
    return {
        restrict:'A',
        link:function (scope, element, attrs) {
            element.bind('blur', function () {
                scope.$eval(attrs.lmBlur);
            });
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

angular.module('lampost_dir').directive('popover', function () {
    return {
        restrict:'A',
        link:function (scope, element, attrs) {
            var args = attrs.popover.split('|');
            var opts = {};
            if (args.length > 1) {
                opts.placement = args[1];
            }
            if (args.length > 2) {
                opts.trigger = args[2];
            }
            element.popover(opts);

            scope.$watch(attrs.popoverTitle + ' + ' + args[0],
                configPopover);
            configPopover();
            function configPopover() {
                var popover = element.data('popover');
                popover.options.title = scope.$eval(attrs.popoverTitle);
                popover.options.content = scope.$eval(args[0]);
            }
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

angular.module('lampost_dir').directive("altText", [function () {
    return {
        restrict:"A",
        link:function (scope, element, attrs) {
            element.attr("title", scope.$eval(attrs.altText));
        }
    }

}]);