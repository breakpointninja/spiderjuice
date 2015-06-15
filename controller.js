(function() {
  'use strict';
  SjCtrl.callbackMap = {};
  SjCtrl.onState = function(state, callback) {
    if (!state) {
      SjCtrl.log_error('No state specified for onState');
    } else {
      SjCtrl.callbackMap[state] = callback;
    }
    return SjCtrl;
  };
  SjCtrl.run = function() {
    var state = SjCtrl.current_state;
    if (SjCtrl.callbackMap.hasOwnProperty(state)) {
      var cb = SjCtrl.callbackMap[state];
      cb();
    } else {
      SjCtrl.log_error('No callback with state ' + state);
    }
    return SjCtrl;
  };
  console.log('Initialized!');
}).call(this);
