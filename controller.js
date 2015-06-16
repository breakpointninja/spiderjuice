(function() {
  'use strict';

  SjCtrl.callbackMap = {};
  SjCtrl.httpRequestCallbackMap = {};
  SjCtrl.httpRequestGenerate = 1;
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
      try {
        cb(SjCtrl.job);
      } catch(e) {
        SjCtrl.log_error('Exception in job: ' + e.message);
        SjCtrl.done();
      }
    } else {
      SjCtrl.log_error('No callback with state ' + state);
    }
    return SjCtrl;
  };

  SjCtrl.getJson = function(url, success_callback, failure_callback, always_callback) {
    SjCtrl.httpRequestGenerate = SjCtrl.httpRequestGenerate + 1;
    SjCtrl.http_request(SjCtrl.httpRequestGenerate, url);
    SjCtrl.httpRequestCallbackMap[SjCtrl.httpRequestGenerate] = [success_callback, failure_callback, always_callback];
  };

  SjCtrl.httpRequestCallback = function(callback_id, error_id, data) {
    var callback = SjCtrl.httpRequestCallbackMap[callback_id];
    if (error_id === 0) {
      console.log(data);
      callback[0](JSON.parse(data));
    } else {
      callback[1](error_id);
    }
    callback[2]();

    SjCtrl.httpRequestCallbackMap.removeAttribute(callback_id);
  };

  SjCtrl.relativeToAbsolute = function(url) {
        if (value.substr(0,1) !== "/") {
          value = window.location.pathname + url;
        }
        return window.location.origin + url;
  };

  SjCtrl.http_request_finished.connect(SjCtrl, 'httpRequestCallback');
}).call(this);
