import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Register from './components/Register';
import Login from './components/Login';
import Home from './components/Home';
import Locations from './components/Locations';
import Hotels from './components/Hotels';
import ProtectedRoute from './components/ProtectedRoute';
import YourBookings from './components/YourBookings';
import BookedVisits from './components/BookedVisits';
import Chatbot from './components/ChatBot';
import Planner from './components/Planner';
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Routes */}
        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />
        <Route
          path="/locations"
          element={
            <ProtectedRoute>
              <Locations />
            </ProtectedRoute>
          }
        />
        <Route
          path="/hotels"
          element={
            <ProtectedRoute>
              <Hotels />
            </ProtectedRoute>
          }
        />
        <Route
          path="/bookings"
          element={
            <ProtectedRoute>
              <YourBookings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/booked-visits"
          element={
            <ProtectedRoute>
              <BookedVisits />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chatbot"
          element={
            <ProtectedRoute>
              <Chatbot />
            </ProtectedRoute>
          }
        />
        <Route
          path="/plans"
          element={
            <ProtectedRoute>
              <Planner />
            </ProtectedRoute>
          }
        />

      </Routes>
    </Router>
  );
}

export default App;
