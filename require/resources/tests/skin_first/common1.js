/*global require */
'use strict';
require.config({
  baseUrl: '/static/js/skin_first'
});
require(['testdir/util'], function (util) {
  util.test();
  console.log('common in first skin running');
});
