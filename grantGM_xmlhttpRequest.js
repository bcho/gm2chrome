/**
 * grantGM_xmlhttpRequest.js
 *
 * Implement GM_xmlhttpRequst[0] with jQuery ajax method.
 *
 * [0](http://wiki.greasespot.net/GM_xmlhttpRequest)
 */

var GM_xmlhttpRequest = function(settings) {
    var nop = function() { return; };

    settings.onload = settings.onload || nop;
    settings.onerror = settings.onerror || nop;

    // For compatibility, provide jqxhr as argument
    // instead of response object.
    //
    // ref: http://api.jquery.com/jQuery.ajax/#jqXHR
    var jqxhr = $.ajax(settings)
        .done(function(resp) {
            settings.onload(jqxhr);
        })
        .fail(function(resp) {
            settings.onerror(jqxhr);
        });
    return jqxhr;
};
