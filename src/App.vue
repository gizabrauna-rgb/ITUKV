<template>
  <component
    :is="currentView"
    :user-name="userName"
    @logged-in="onLoggedIn"
    @logout="onLogout"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Login from './views/Login.vue'
import AdminDashboard from './views/AdminDashboard.vue'
import TargetDashboard from './views/TargetDashboard.vue'
import InvestorDashboard from './views/InvestorDashboard.vue'

const role = ref(sessionStorage.getItem('userRole') || '')
const userName = ref(sessionStorage.getItem('userName') || '')

const currentView = computed(() => {
  if (!role.value) return Login
  if (role.value === 'admin') return AdminDashboard
  if (role.value === 'target') return TargetDashboard
  if (role.value === 'investor') return InvestorDashboard
  return Login
})

function onLoggedIn(user) {
  role.value = user.role
  userName.value = user.name
}

function onLogout() {
  role.value = ''
  userName.value = ''
}
</script>
