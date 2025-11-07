import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import API from '../api';
import '../styles/bookings.css';

function YourBookings() {
  const [homeBookings, setHomeBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchHomeBookings = async () => {
    try {
      const res = await API.get('/bookings/homes/');
      setHomeBookings(res.data);
    } catch (error) {
      console.error('Error fetching home bookings:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHomeBookings();
  }, []);

  const handleDelete = async (id) => {
    const confirmDelete = window.confirm('Are you sure you want to cancel this booking?');
    if (!confirmDelete) return;
    try {
      await API.delete(`/bookings/homes/${id}/`);
      alert('Booking cancelled successfully.');
      setHomeBookings(homeBookings.filter((b) => b.id !== id));
    } catch (error) {
      console.error('Error cancelling booking:', error);
      alert('Failed to cancel booking. Please try again.');
    }
  };

  const handleProceed = (booking) => {
    // Calculate the total cost
    const checkIn = new Date(booking.check_in_date);
    const checkOut = new Date(booking.check_out_date);
    const nights = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));
    const totalCost = booking.average_cost * nights;

    alert(
      `Booking Details:\n\n` +
      `Hotel: ${booking.home_name}\n` +
      `Check-in: ${booking.check_in_date}\n` +
      `Check-out: ${booking.check_out_date}\n` +
      `Nights: ${nights}\n` +
      `Guests: ${booking.number_of_guests}\n` +
      `Cost per night: ₹${booking.average_cost}\n` +
      `Total Cost: ₹${totalCost}\n\n` +
      `Your booking is confirmed! Enjoy your stay!`
    );
  };

  return (
    <div>
      <Navbar />
      <div className="bookings-page">
        <header className="bookings-header">
          <h1>Your Hotel Bookings</h1>
          <p>Manage your upcoming stays</p>
        </header>

        {loading ? (
          <div className="loading-state">Loading your bookings...</div>
        ) : homeBookings.length === 0 ? (
          <div className="empty-state">
            <h3>No hotel bookings found</h3>
            <p>Your future hotel bookings will appear here</p>
          </div>
        ) : (
          <div className="bookings-grid">
            {homeBookings.map((booking) => (
              <div key={booking.id} className="booking-card">
                <h3 className="booking-title">{booking.home_name}</h3>
                
                <div className="booking-info">
                  <i className="fas fa-calendar-check"></i>
                  Check-in: {booking.check_in_date}
                </div>
                
                <div className="booking-info">
                  <i className="fas fa-calendar-times"></i>
                  Check-out: {booking.check_out_date}
                </div>
                
                <div className="booking-info">
                  <i className="fas fa-users"></i>
                  {booking.number_of_guests} Guests
                </div>

                <div className={`booking-status status-${booking.status.toLowerCase()}`}>
                  {booking.status}
                </div>

                <div className="booking-cost">
                  ₹{booking.average_cost} <span className="price-note">per night</span>
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

export default YourBookings;
