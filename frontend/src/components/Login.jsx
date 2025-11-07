import React, { useState } from 'react';
import API from '../api';
import { useNavigate, Link } from 'react-router-dom';
import '../styles/common.css';
import '../styles/forms.css';

function Login() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await API.post('/accounts/login/', formData);
      localStorage.setItem('access', res.data.access);
      localStorage.setItem('refresh', res.data.refresh);
      navigate('/home');
    } catch (error) {
      setError('Invalid email or password');
    }
  };

  return (
    <div className="form-container">
      <h2 className="form-title">Welcome Back</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="email">Email</label>
          <input
            id="email"
            className="form-input"
            type="email"
            name="email"
            placeholder="Enter your email"
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="password">Password</label>
          <input
            id="password"
            className="form-input"
            type="password"
            name="password"
            placeholder="Enter your password"
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" className="form-button">Sign In</button>
      </form>
      <Link to="/register" className="form-link">
        Don't have an account? Register now
      </Link>
    </div>
  );
}

export default Login;
