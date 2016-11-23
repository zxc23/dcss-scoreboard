import Vue from 'vue'
import axios from 'axios'
import VueAxios from 'vue-axios'
import App from './App'

Vue.use(VueAxios, axios)

/* eslint-disable no-new */
new Vue({
  el: '#app',
  template: '<App></App>',
  components: { App }
})
