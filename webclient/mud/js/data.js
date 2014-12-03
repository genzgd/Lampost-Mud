angular.module('lampost_mud').service('lmData', ['lpEvent', 'lpUtil', function (lpEvent, lpUtil) {

  var maxLines = 1000;
  var unreadCount = 0;
  var self = this;
  var title = lampost_config.title;

  self.defaultDisplays = {};
  self.channels = {};
  self.status = {};

  clear();

  function clear() {

    self.display = [];
    self.userId = 0;
    self.playerIds = [];
    self.playerId = 0;
    self.playerList = {};
    self.immLevel = null;
    self.history = [];
    self.historyIx = 0;
    self.userDisplays = {};
    self.notifies = [];
    self.validTabs = ['channel', 'playerList'];
    self.messages = [];
    clearUnread();
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
    unreadCount += lines.length;
    jQuery('title').text('[' + unreadCount + '] ' + title);
    lpEvent.dispatch("display_update");
  }

  function channelSubscribe(channel) {
    self.channels[channel.id] = channel.messages;
    lpEvent.dispatch("sort_channels");
  }

  function channelUnsubscribe(channel_id) {
    delete self.channels[channel_id];
    lpEvent.dispatch("sort_channels");
  }

  function updateChannel(channelMessage) {
    self.channels[channelMessage.id].push(channelMessage);
    updateDisplay({lines: [{text: channelMessage.text, display: channelMessage.id + "_channel"}]});
  }

  function setUser(data) {
    self.userId = data.user_id;
    self.playerIds = data.player_ids;
    self.notifies = data.notifies;
    if (data.password_reset) {
      lpEvent.dispatch('password_reset');
    }
  }

  function clearUnread() {
    unreadCount = 0;
    jQuery('title').text(title);
  }

  this.adjustLine = function (line, display) {
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

  lpEvent.register('client_config', function (data) {
    self.defaultDisplays = data.default_displays;
  });

  lpEvent.register("login", function (data) {
    setUser(data);
    self.playerName = data.name;
    self.userDisplays = data.displays;
    self.immLevel = data.imm_level;
    self.playerId = self.playerName.toLocaleLowerCase();
    self.validTabs = ['status', 'channel', 'messages', 'playerList'];
    self.messages = data.messages;

    lpUtil.intSort(self.messages, 'msg_id');
  }, null, -100);

  lpEvent.register('player_update', function(data) {
    self.immLevel = data.imm_level;
  }, null, -100);

  lpEvent.register("user_login", setUser, null, -100);
  lpEvent.register("display", updateDisplay, null, -100);
  lpEvent.register("channel", updateChannel, null, -100);
  lpEvent.register("channel_subscribe", channelSubscribe, null, -100);
  lpEvent.register("channel_unsubscribe", channelUnsubscribe, null, -100);
  lpEvent.register("user_activity", clearUnread);
  lpEvent.register("status", function (status) {
    self.status = status;
  });
  lpEvent.register("logout", clear, null, -100);

  lpEvent.register("new_message", function (message) {
    self.messages.push(message);
  }, null, -100);

  lpEvent.register("player_list", function (playerList) {
    self.playerList = playerList;
    lpEvent.dispatch('player_list_update');
  });

}]);

