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
        cb(SjCtrl.job_dict);
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

    SjCtrl.remove_undefined = function(obj) {
        if (typeof obj === "undefined") {
            return undefined;
        }
        if (obj instanceof Array) {
            var new_obj = [];
        } else {
            var new_obj = {};
        }
        for (var property in obj) {
            if (obj.hasOwnProperty(property)) {
                if (typeof obj[property] === "object") {
                    var ret = SjCtrl.remove_undefined(obj[property]);
                    if (typeof ret === "undefined") {
                        continue;
                    }
                    if (new_obj instanceof Array) {
                        new_obj.push(ret);
                    } else {
                        new_obj[property] = ret;
                    }
                } else if (typeof obj[property] !== "undefined") {
                    if (typeof obj[property] === "undefined") {
                        continue;
                    }
                    if (new_obj instanceof Array) {
                        new_obj.push(obj[property]);
                    } else {
                        new_obj[property] = obj[property];
                    }
                }
            }
        }
        return new_obj;
    };

    SjCtrl.post_obj = function(url, obj) {
        SjCtrl.post_request(url, JSON.stringify(SjCtrl.remove_undefined(obj)));
    };

  SjCtrl.relativeToAbsolute = function(href) {
      if (typeof href === 'string' && href.length !== 0) {
          var link = document.createElement("a");
          link.href = href;
          return (link.protocol + "//" + link.host + link.pathname + link.search + link.hash);
      } else {
          return href;
      }
  };

  SjCtrl.http_request_finished.connect(SjCtrl, 'httpRequestCallback');
}).call(this);
