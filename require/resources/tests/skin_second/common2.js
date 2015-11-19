/*global require, define */
'use strict';
require.config({
  baseUrl: '/static/js/skin_second'
});
define('common2', ['testdir/util'], function (util) {
  util.test();
  console.debug('common in second skin running');
});
