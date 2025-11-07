import React, { useState } from 'react';
import API from '../api';
import { useNavigate, Link } from 'react-router-dom';
import '../styles/common.css';
import '../styles/forms.css';

function Register() {
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    password: '',
    password2: '',
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.password2) {
      setError('Passwords do not match');
      return;
    }
    try {
      await API.post('/accounts/register/', formData);
      alert('Registration successful!');
      navigate('/');
    } catch (error) {
      setError('Registration failed. Please try again.');
    }
  };

  return (
    <div className="form-container">
      <h2 className="form-title">Create Account</h2>
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
          <label className="form-label" htmlFor="name">Full Name</label>
          <input
            id="name"
            className="form-input"
            type="text"
            name="name"
            placeholder="Enter your full name"
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
            placeholder="Choose a password"
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="password2">Confirm Password</label>
          <input
            id="password2"
            className="form-input"
            type="password"
            name="password2"
            placeholder="Confirm your password"
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" className="form-button">Sign Up</button>
      </form>
      <Link to="/" className="form-link">
        Already have an account? Sign in
      </Link>
    </div>
  );
}

export default Register;
