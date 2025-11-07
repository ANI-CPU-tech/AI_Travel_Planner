import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000/api',
});

API.interceptors.request.use((config) => {
  // Do not attach Authorization header for public AI endpoints to avoid
  // triggering 401 responses from the backend when the local access token
  // is expired or invalid. Those endpoints support anonymous requests.
  const publicPaths = ['/assistant/classify/', '/assistant/search/', '/planner/plans/generate/'];
  const reqUrl = config.url || '';
  const base = API.defaults && API.defaults.baseURL ? API.defaults.baseURL : '';
  // derive the request path portion
  let path = reqUrl;
  try {
    if (reqUrl.startsWith(base)) {
      path = reqUrl.slice(base.length);
    }
  } catch (e) {
    // ignore
  }

  const isPublic = publicPaths.some(p => path.endsWith(p) || reqUrl.endsWith(p) || path === p);
  // Attach token only when present and not expired. For public endpoints we
  // intentionally DO NOT attach the Authorization header to avoid triggering
  // authentication errors on the backend; public endpoints work anonymously.
  const token = localStorage.getItem('access');
  let attach = false;
  if (token) {
    try {
      const parts = token.split('.');
      if (parts.length === 3) {
        const payload = JSON.parse(window.atob(parts[1]));
        if (payload && payload.exp && payload.exp * 1000 > Date.now()) {
          attach = true;
        }
      }
    } catch (e) {
      attach = false;
    }
  }

  // Only attach token for non-public endpoints. This guarantees classify/generate
  // calls are anonymous when the token is expired or even when valid (to avoid
  // accidental 401s). If you want logged-in personalization for these endpoints
  // later, we can add an explicit opt-in.
  if (!isPublic && attach) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

API.interceptors.response.use(
  (response) => response, 
  async (error) => {
    const originalRequest = error.config;
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refresh = localStorage.getItem('refresh');
        if (!refresh) throw new Error('No refresh token found');

        // refresh token
        const res = await axios.post('http://localhost:8000/api/token/refresh/', {
          refresh: refresh,
        });

        // store new tokens
        localStorage.setItem('access', res.data.access);

        // attach new access token to retry request
        originalRequest.headers.Authorization = `Bearer ${res.data.access}`;

        // retry original request
        return API(originalRequest);
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        // remove tokens & redirect to login
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
        window.location.href = '/';
      }
    }

    // reject other errors
    return Promise.reject(error);
  }
);

export default API;
