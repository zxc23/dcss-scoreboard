import Vue from 'vue'
import axios from 'axios'
import VueAxios from 'vue-axios'
import App from './App'
import VueTables from 'vue-tables-2'

Vue.use(VueAxios, axios)
Vue.use(VueTables.client)

/* eslint-disable no-new */
new Vue({
  el: '#app',
  template: '<App></App>',
  components: { App }
})
