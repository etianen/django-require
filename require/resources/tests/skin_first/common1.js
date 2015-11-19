/*global require, define */
'use strict';
require.config({
  baseUrl: '/static/js/skin_first'
});
define('common1', ['testdir/util'], function (util) {
  util.test();
  console.log('common in first skin running');
});
