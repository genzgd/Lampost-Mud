angular.module('lampost').service('lmComm', ['lmBus', 'lmData', 'lmDialog', function(lmBus, lmData, lmDialog) {

    var self = this;
    lmBus.register('friend_login', friendLogin);

    function friendLogin(friend_info) {
        if (lmData.notifies.indexOf('friendNotify') > -1) {
            self.notify({icon: 'image/friendNotify.png', title: "Your friend " +  friend_info.name + " logged into " + lampost_config.title, content: ''});
        }
        if (lmData.notifies.indexOf('friendSound') > -1) {
            jQuery('#sound_beep_ping')[0].play();
        }
    }

    function showNotification(notify_data) {
         var notification = window.webkitNotifications.createNotification(notify_data.icon, notify_data.title, notify_data.content);
         notification.show();
    }

    this.requestNotificationPermission = function(notify_data) {
         lmDialog.showConfirm("Allow Notifications", "You must grant permission to allow notifications from " + lampost_config.title, function() {
            window.webkitNotifications.requestPermission(function() {
                self.notify(notify_data);
            })
         });
    };

    this.notify = function(notify_data) {
        if (!window.webkitNotifications) {
            return;
        }
        var permLevel = window.webkitNotifications.checkPermission();
        if (permLevel == 0) {
            showNotification(notify_data);
        } else if (permLevel == 1) {
            self.requestNotificationPermission(notify_data);
        }
    }

}]);