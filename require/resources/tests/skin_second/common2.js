/*global require */
'use strict';
require.config({
  baseUrl: '/static/js/skin_second'
});
require(['testdir/util'], function (util) {
  util.test();
  console.debug('common in second skin running');
});
