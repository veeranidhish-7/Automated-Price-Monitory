import axios from "axios";

const API_URL = "http://localhost:5000/api";

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add token to requests automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth APIs
export const register = (email, password) =>
  api.post("/auth/register", { email, password });

export const login = (email, password) =>
  api.post("/auth/login", { email, password });

// Product APIs
export const getProducts = () => api.get("/products");

export const addProduct = (url, target_price) =>
  api.post("/products", { url, target_price });

export const deleteProduct = (productId) =>
  api.delete(`/products/${productId}`);

export default api;
