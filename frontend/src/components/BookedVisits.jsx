import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import API from '../api';
import '../styles/bookings.css';

function BookedVisits() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchBookings = async () => {
    try {
      const res = await API.get('/bookings/locations/');
      setBookings(res.data);
    } catch (error) {
      console.error('Error fetching booked visits:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, []);

  const handleDelete = async (id) => {
    const confirmDelete = window.confirm('Are you sure you want to cancel this visit?');
    if (!confirmDelete) return;
    try {
      await API.delete(`/bookings/locations/${id}/`);
      alert('Visit cancelled successfully.');
      setBookings(bookings.filter((b) => b.id !== id));
    } catch (error) {
      console.error('Error cancelling visit:', error);
      alert('Failed to cancel visit. Please try again.');
    }
  };

  const handleProceed = (booking) => {
    // Show visit details and confirmation
    alert(
      `Visit Details:\n\n` +
      `Location: ${booking.location_name}\n` +
      `Date: ${booking.travel_date}\n` +
      `Group Size: ${booking.number_of_people} people\n` +
      `Estimated Cost: ₹${booking.average_cost || 'N/A'}\n\n` +
      `Your visit is confirmed! Have a great trip!`
    );
  };

  return (
    <div>
      <Navbar />
      <div className="bookings-page">
        <header className="bookings-header">
          <h1>Your Booked Visits</h1>
          <p>Manage your upcoming travel plans</p>
        </header>

        {loading ? (
          <div className="loading-state">Loading your visits...</div>
        ) : bookings.length === 0 ? (
          <div className="empty-state">
            <h3>No visits booked yet</h3>
            <p>Your planned visits to locations will appear here</p>
          </div>
        ) : (
          <div className="bookings-grid">
            {bookings.map((booking) => (
              <div key={booking.id} className="booking-card">
                <h3 className="booking-title">{booking.location_name}</h3>
                
                <div className="booking-info">
                  <i className="fas fa-calendar"></i>
                  Travel Date: {booking.travel_date}
                </div>
                
                <div className="booking-info">
                  <i className="fas fa-users"></i>
                  {booking.number_of_people} People
                </div>

                <div className={`booking-status status-${booking.status.toLowerCase()}`}>
                  {booking.status}
                </div>

                <div className="booking-cost">
                  ₹{booking.average_cost || 'Cost TBD'}
                  {booking.average_cost && <span className="price-note"> estimated</span>}
                </div>

                <div className="booking-date">
                  Booked on: {new Date(booking.booking_date).toLocaleDateString()}
                </div>

                <div className="booking-actions">
                  <button className="btn btn-proceed" onClick={() => handleProceed(booking)}>
                    <i className="fas fa-check-circle"></i>
                    Proceed
                  </button>
                  <button className="btn btn-delete" onClick={() => handleDelete(booking.id)}>
                    <i className="fas fa-times-circle"></i>
                    Cancel
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default BookedVisits;
