import React, { useEffect, useState } from 'react';
import Navbar from './Navbar';
import API from '../api';
import '../styles/common.css';
import '../styles/planner.css';

function Planner() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const res = await API.get('/planner/plans/');
        setPlans(res.data || []);
      } catch (err) {
        console.error('Failed to load plans', err);
        setError('Failed to load plans.');
      } finally {
        setLoading(false);
      }
    };
    fetchPlans();
  }, []);

  return (
    <div>
      <Navbar />
      <div className="planner-container">
        <h2 className="planner-header">Your Travel Plans</h2>
        {loading && <div className="loading">Loading your plans...</div>}
        {error && <div className="error-message">{error}</div>}
        {!loading && plans.length === 0 && (
          <div className="empty-state">
            No plans saved yet. Try using our AI Assistant to create a plan!
          </div>
        )}
        <div className="plan-grid">
          {plans.map((p) => (
            <div key={p.id} className="plan-card">
              <h3 className="plan-title">{p.title || `Plan ${p.id}`}</h3>
              {p.start_date && p.end_date && (
                <div className="plan-dates">
                  {p.start_date} → {p.end_date}
                </div>
              )}
              <div className="plan-summary">{p.summary}</div>
              <details className="plan-details">
                <summary>View Itinerary</summary>
                <pre>{JSON.stringify(p.itinerary, null, 2)}</pre>
              </details>
              <div className="plan-action">
                <button
                  className="plan-button"
                  onClick={() => {
                    window.location.href = `/booking?plan=${p.id}`;
                  }}
                >
                  Proceed to Book
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Planner;
