angular.module('lampost').service('lmData', ['lmBus', 'lmUtil', function(lmBus, lmUtil) {

    var maxLines = 1000;
    var self = this;

    self.defaultDisplays = {};
    self.channels = {};

    clear();

    function clear() {

        if (self.editorWindow && !self.editorWindow.closed) {
            self.editorWindow.close();
            delete self.editorWindow;
        }

        self.display = [];
        self.userId = 0;
        self.playerIds = [];
        self.editors = [];
        self.playerId = 0;
        self.playerList = {};
        self.history = [];
        self.historyIx = 0;
        self.editorWindow = null;
        self.userDisplays = {};
        self.notifies = [];
        self.validTabs = ['channel', 'playerList'];
        self.messages = [];
    }

    function displayLine(line) {
        self.adjustLine(line);
        self.display.push(line);
        if (self.display.length > maxLines) {
            self.display.splice(0, self.display.length - maxLines);
        }
    }

    function updateDisplay(display) {
        var lines = display.lines;
        for (var i = 0; i < lines.length; i++) {
            displayLine(lines[i]);
        }
        lmBus.dispatch("display_update", display);
    }

    function rebuildChannels(channels) {
        self.channels = {};
        angular.forEach(channels, function(channel) {
            self.channels[channel.id] = channel.messages;
        });
        lmBus.dispatch("channels");
    }

    function updateChannel(channelMessage) {
        displayLine({text: channelMessage.text, display: channelMessage.id + "_channel"});
        self.channels[channelMessage.id].push(channelMessage);
    }

    function setUser(data) {
        self.userId = data.user_id;
        self.playerIds = data.player_ids;
        self.notifies = data.notifies;
        if (data.password_reset) {
            lmBus.dispatch('password_reset');
        }
    }

    this.adjustLine = function(line, display) {
        display = display || line.display;
        var lineDisplay = self.userDisplays[display] || self.defaultDisplays[display];
        if (!lineDisplay) {
            return;
        }
        if (line.text == 'HRT') {
            line.style = {height: '2px', backgroundColor: lineDisplay.color, marginTop: '6px', marginBottom: '3px', marginRight: '3px'};
            line.text = '';
        } else if (line.text == "HRB") {
            line.style = {height: '2px', backgroundColor: lineDisplay.color, marginTop: '3px', marginBottom: '6px', marginRight: '3px'};
            line.text = '';
        } else {
            line.style = {color: lineDisplay.color};
        }
    };

    lmBus.register('client_config', function(data) {
        self.defaultDisplays = data.default_displays;
    });

    lmBus.register("login", function(data) {
        setUser(data);
        rebuildChannels(data.channels);
        self.editors = data.editors;
        self.playerIds = data.player_ids;
        self.playerName = data.name;
        self.userDisplays = data.displays;
        self.playerId = self.playerName.toLocaleLowerCase();
        self.validTabs = ['status', 'channel', 'messages', 'playerList'];
        self.messages = data.messages;

        lmUtil.intSort(self.messages, 'msg_id');
        localStorage.setItem("lm_editors_" + self.playerId, JSON.stringify(self.editors));
    }, null, -100);

    lmBus.register("user_login", setUser, null, -100);
    lmBus.register("display", updateDisplay, null, -100);
    lmBus.register("channel", updateChannel, null, -100);
    lmBus.register("gen_channels", rebuildChannels, null, -100);
    lmBus.register("logout", clear, null, -100);

    lmBus.register("new_message", function(message) {
        self.messages.push(message);
    }, null, -100);

    lmBus.register("player_list", function (playerList) {
        self.playerList = playerList;
        lmBus.dispatch('player_list_update');
    });

}]);

