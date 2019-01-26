// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import KoreanParser from './KoreanParser'

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#korean-parser',
  components: { KoreanParser, },
  template: '<KoreanParser/>'
})
