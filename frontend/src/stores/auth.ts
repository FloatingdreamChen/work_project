import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || '',
    refreshToken: localStorage.getItem('refresh_token') || '',
    username: localStorage.getItem('username') || '',
    role: localStorage.getItem('role') || 'user',
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
  },
  actions: {
    setSession(token: string, refreshToken: string, username: string, role = 'user') {
      this.token = token
      this.refreshToken = refreshToken
      this.username = username
      this.role = role
      localStorage.setItem('access_token', token)
      localStorage.setItem('refresh_token', refreshToken)
      localStorage.setItem('username', username)
      localStorage.setItem('role', role)
    },
    logout() {
      this.token = ''
      this.refreshToken = ''
      this.username = ''
      this.role = 'user'
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
    },
  },
})
