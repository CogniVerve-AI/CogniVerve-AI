import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth service
export const authService = {
  login: async (credentials) => {
    const response = await api.post('/api/v1/auth/login', credentials)
    return response.data
  },

  register: async (userData) => {
    const response = await api.post('/api/v1/auth/register', userData)
    return response.data
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/v1/auth/me')
    return response.data
  },
}

// Agents service
export const agentsService = {
  getAgents: async (page = 1, size = 10) => {
    const response = await api.get(`/api/v1/agents?page=${page}&size=${size}`)
    return response.data
  },

  getAgent: async (agentId) => {
    const response = await api.get(`/api/v1/agents/${agentId}`)
    return response.data
  },

  createAgent: async (agentData) => {
    const response = await api.post('/api/v1/agents', agentData)
    return response.data
  },

  updateAgent: async (agentId, agentData) => {
    const response = await api.put(`/api/v1/agents/${agentId}`, agentData)
    return response.data
  },

  deleteAgent: async (agentId) => {
    const response = await api.delete(`/api/v1/agents/${agentId}`)
    return response.data
  },

  cloneAgent: async (agentId) => {
    const response = await api.post(`/api/v1/agents/${agentId}/clone`)
    return response.data
  },
}

// Tasks service
export const tasksService = {
  getTasks: async (page = 1, size = 10, status = null) => {
    let url = `/api/v1/tasks?page=${page}&size=${size}`
    if (status) {
      url += `&status_filter=${status}`
    }
    const response = await api.get(url)
    return response.data
  },

  getTask: async (taskId) => {
    const response = await api.get(`/api/v1/tasks/${taskId}`)
    return response.data
  },

  createTask: async (taskData) => {
    const response = await api.post('/api/v1/tasks', taskData)
    return response.data
  },

  cancelTask: async (taskId) => {
    const response = await api.post(`/api/v1/tasks/${taskId}/cancel`)
    return response.data
  },

  getTaskLogs: async (taskId) => {
    const response = await api.get(`/api/v1/tasks/${taskId}/logs`)
    return response.data
  },

  getTaskArtifacts: async (taskId) => {
    const response = await api.get(`/api/v1/tasks/${taskId}/artifacts`)
    return response.data
  },
}

// Conversations service
export const conversationsService = {
  getConversations: async (page = 1, size = 10) => {
    const response = await api.get(`/api/v1/conversations?page=${page}&size=${size}`)
    return response.data
  },

  getConversation: async (conversationId) => {
    const response = await api.get(`/api/v1/conversations/${conversationId}`)
    return response.data
  },

  createConversation: async (conversationData) => {
    const response = await api.post('/api/v1/conversations', conversationData)
    return response.data
  },

  updateConversation: async (conversationId, conversationData) => {
    const response = await api.put(`/api/v1/conversations/${conversationId}`, conversationData)
    return response.data
  },

  deleteConversation: async (conversationId) => {
    const response = await api.delete(`/api/v1/conversations/${conversationId}`)
    return response.data
  },

  getMessages: async (conversationId, page = 1, size = 50) => {
    const response = await api.get(`/api/v1/conversations/${conversationId}/messages?page=${page}&size=${size}`)
    return response.data
  },

  createMessage: async (conversationId, messageData) => {
    const response = await api.post(`/api/v1/conversations/${conversationId}/messages`, messageData)
    return response.data
  },
}

// Tools service
export const toolsService = {
  getTools: async (page = 1, size = 20, category = null, search = null) => {
    let url = `/api/v1/tools?page=${page}&size=${size}`
    if (category) url += `&category=${category}`
    if (search) url += `&search=${search}`
    const response = await api.get(url)
    return response.data
  },

  getTool: async (toolName) => {
    const response = await api.get(`/api/v1/tools/${toolName}`)
    return response.data
  },

  getToolSchema: async (toolName) => {
    const response = await api.get(`/api/v1/tools/${toolName}/schema`)
    return response.data
  },

  testTool: async (toolName, parameters) => {
    const response = await api.post(`/api/v1/tools/${toolName}/test`, parameters)
    return response.data
  },

  getToolCategories: async () => {
    const response = await api.get('/api/v1/tools/categories/list')
    return response.data
  },
}

export default api

