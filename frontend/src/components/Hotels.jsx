import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import API from '../api';
import '../styles/common.css';
import '../styles/hotels.css';

function Hotels() {
  const [homes, setHomes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedHome, setSelectedHome] = useState(null);
  const [checkInDate, setCheckInDate] = useState('');
  const [checkOutDate, setCheckOutDate] = useState('');
  const [numberOfGuests, setNumberOfGuests] = useState(1);

  // Fetch all hotels (homes)
  const fetchHomes = async () => {
    try {
      const res = await API.get('/homes/');
      setHomes(res.data);
    } catch (error) {
      console.error('Error fetching homes:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHomes();
  }, []);

  // When user clicks "Book Now"
  const handleBookNow = (home) => {
    setSelectedHome(home);
  };

  // Confirm booking
  const handleConfirmBooking = async () => {
    if (!checkInDate || !checkOutDate) {
      alert('Please select both check-in and check-out dates.');
      return;
    }
    if (numberOfGuests <= 0) {
      alert('Number of guests must be at least 1.');
      return;
    }

    try {
      await API.post('/bookings/homes/', {
        home: selectedHome.id,
        check_in_date: checkInDate,
        check_out_date: checkOutDate,
        number_of_guests: numberOfGuests,
      });

      alert(`Booking confirmed for ${selectedHome.location_name}!`);
      setSelectedHome(null);
      setCheckInDate('');
      setCheckOutDate('');
      setNumberOfGuests(1);
    } catch (error) {
      console.error('Error creating home booking:', error);
      alert('Failed to book the home. Please try again.');
    }
  };

  return (
    <div>
      <Navbar />
      <div className="hotels-page">
        <header className="hotels-header">
          <h1>Find Your Perfect Stay</h1>
          <p>Discover comfortable and luxurious accommodations</p>
        </header>

        {loading ? (
          <div className="loading">Loading available hotels...</div>
        ) : homes.length === 0 ? (
          <div className="empty-state">No hotels available at the moment</div>
        ) : (
          <div className="locations-grid">
            {homes.map((home) => (
              <div key={home.id} className="hotel-card">
                <div className="card-image-container">
                  {home.location_image && (
                    <img
                      className="card-image"
                      src={
                        home.location_image.startsWith('http')
                          ? home.location_image
                          : `http://localhost:8000/media/locations/${home.location_image}`
                      }
                      alt={home.location_name}
                      loading="lazy"
                      onError={(e) => {
                        e.target.src = '/placeholder-hotel.jpg';
                        e.target.onerror = null;
                      }}
                    />
                  )}
                  {home.category && (
                    <span className="card-badge">{home.category}</span>
                  )}
                </div>

                <div className="card-content">
                  <h3 className="card-title">{home.location_name}</h3>
                  <div className="card-info">
                    <span>{home.city}, {home.country}</span>
                  </div>
                  
                  <div className="hotel-amenities">
                    <span className="amenity-tag">🛏️ Comfy Beds</span>
                    <span className="amenity-tag">🏊‍♂️ Pool</span>
                    <span className="amenity-tag">🅿️ Parking</span>
                    {home.best_time_to_visit && (
                      <span className="amenity-tag">📅 Best Time: {home.best_time_to_visit}</span>
                    )}
                  </div>

                  <div className="card-rating">
                    <span className="rating-stars">
                      {[...Array(5)].map((_, index) => {
                        const rating = parseFloat(home.rating) || 0;
                        return (
                          <span key={index} style={{ color: index < rating ? '#FFB800' : '#E2E8F0' }}>
                            ★
                          </span>
                        );
                      })}
                    </span>
                    <span className="rating-number">
                      {home.rating ? parseFloat(home.rating).toFixed(1) : 'N/A'}
                    </span>
                  </div>

                  <div className="booking-details">
                    <div className="price-per-night">
                      ₹{home.average_cost || 'N/A'}
                      <span className="price-note"> per night</span>
                    </div>
                    <button
                      className="button confirm-button"
                      onClick={() => handleBookNow(home)}
                    >
                      Book Now
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Booking Modal */}
        {selectedHome && (
          <div className="booking-overlay">
            <div className="booking-form">
              <div className="modal-header">
                <h2>Book Your Stay</h2>
                <button className="close-button" onClick={() => setSelectedHome(null)}>×</button>
              </div>

              <div className="card-content">
                <h3>{selectedHome.location_name}</h3>
                <p>{selectedHome.city}, {selectedHome.country}</p>
              </div>

              <div className="form-group date-inputs">
                <div>
                  <label htmlFor="check-in">Check-in Date</label>
                  <input
                    id="check-in"
                    className="form-input"
                    type="date"
                    value={checkInDate}
                    onChange={(e) => setCheckInDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>

                <div>
                  <label htmlFor="check-out">Check-out Date</label>
                  <input
                    id="check-out"
                    className="form-input"
                    type="date"
                    value={checkOutDate}
                    onChange={(e) => setCheckOutDate(e.target.value)}
                    min={checkInDate || new Date().toISOString().split('T')[0]}
                  />
                </div>
              </div>

              <div className="form-group guest-select">
                <label htmlFor="guests">Number of Guests</label>
                <input
                  id="guests"
                  className="form-input"
                  type="number"
                  min="1"
                  max="10"
                  value={numberOfGuests}
                  onChange={(e) => setNumberOfGuests(e.target.value)}
                />
              </div>

              <div className="booking-summary">
                <div className="summary-row">
                  <span>Price per night</span>
                  <span>₹{selectedHome.average_cost || 'N/A'}</span>
                </div>
                <div className="summary-row">
                  <span>Number of nights</span>
                  <span>{checkInDate && checkOutDate ? 
                    Math.ceil((new Date(checkOutDate) - new Date(checkInDate)) / (1000 * 60 * 60 * 24)) : 
                    0}</span>
                </div>
                <div className="summary-row summary-total">
                  <span>Total</span>
                  <span>₹{checkInDate && checkOutDate && selectedHome.average_cost ? 
                    selectedHome.average_cost * Math.ceil((new Date(checkOutDate) - new Date(checkInDate)) / (1000 * 60 * 60 * 24)) : 
                    'N/A'}</span>
                </div>
              </div>

              <div className="booking-actions">
                <button className="confirm-button" onClick={handleConfirmBooking}>
                  Confirm Booking
                </button>
                <button className="cancel-button" onClick={() => setSelectedHome(null)}>
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Hotels;
