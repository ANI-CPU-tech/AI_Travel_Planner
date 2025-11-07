import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import API from '../api';
import '../styles/common.css';
import '../styles/locations.css';

function Locations() {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [travelDate, setTravelDate] = useState('');
  const [numberOfPeople, setNumberOfPeople] = useState(1);

  const fetchLocations = async () => {
    try {
      const res = await API.get('/locations/');
      console.log('Locations data:', res.data);
      // Log the first location's image path for debugging
      if (res.data.length > 0) {
        console.log('First location image path:', res.data[0].location_image);
      }
      setLocations(res.data);
    } catch (error) {
      console.error('Error fetching locations:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLocations();
  }, []);

  // When user clicks Visit Now
  const handleVisitNow = (loc) => {
    setSelectedLocation(loc);
  };

  // Confirm booking
  const handleConfirmVisit = async () => {
    if (!travelDate) {
      alert('Please select a travel date.');
      return;
    }
    if (numberOfPeople <= 0) {
      alert('Number of people must be at least 1.');
      return;
    }

    try {
      await API.post('/bookings/locations/', {
        location: selectedLocation.id,
        travel_date: travelDate,
        number_of_people: numberOfPeople,
      });

      alert(`Visit booked successfully for ${selectedLocation.location_name}!`);
      setSelectedLocation(null);
      setTravelDate('');
      setNumberOfPeople(1);
    } catch (error) {
      console.error('Error creating booking:', error);
      alert('Failed to book visit. Please try again.');
    }
  };

  return (
    <div>
      <Navbar />
      <div className="locations-page">
        <header className="locations-header">
          <h1>Explore Amazing Destinations</h1>
          <p>Discover the world's most breathtaking locations</p>
        </header>

        {loading ? (
          <div className="loading">Loading amazing destinations...</div>
        ) : locations.length === 0 ? (
          <div className="empty-state">No locations found</div>
        ) : (
          <div className="locations-grid">
            {locations.map((loc) => (
              <div key={loc.id} className="location-card">
                <div className="card-image-container">
                  {loc.location_image ? (
                    <img
                      className="card-image"
                      src={
                        loc.location_image.startsWith('http')
                          ? loc.location_image
                          : `http://localhost:8000/media/${loc.location_image}`
                      }
                      alt={loc.location_name}
                      loading="lazy"
                      onLoad={(e) => {
                        console.log('Image loaded successfully:', e.target.src);
                      }}
                      onError={(e) => {
                        console.error('Image failed to load:', e.target.src);
                        e.target.src = '/placeholder-location.jpg';
                        e.target.onerror = null;
                      }}
                    />
                  ) : (
                    <img
                      className="card-image"
                      src="/placeholder-location.jpg"
                      alt={`${loc.location_name} placeholder`}
                    />
                  )}
                  {loc.category && (
                    <span className="card-badge">{loc.category}</span>
                  )}
                </div>

                <div className="card-content">
                  <h3 className="card-title">{loc.location_name}</h3>
                  <div className="card-info">
                    <span>{loc.city}, {loc.country}</span>
                  </div>
                  <div className="card-info">
                    Best Time: {loc.best_time_to_visit || 'Anytime'}
                  </div>
                  <div className="card-rating">
                    <span className="rating-stars">
                      {[...Array(5)].map((_, index) => {
                        const rating = parseFloat(loc.rating) || 0;
                        return (
                          <span key={index} style={{ color: index < rating ? '#FFB800' : '#E2E8F0' }}>
                            ★
                          </span>
                        );
                      })}
                    </span>
                    <span className="rating-number">
                      {loc.rating ? parseFloat(loc.rating).toFixed(1) : 'N/A'}
                    </span>
                  </div>
                  <div className="card-price">
                    From ₹{loc.average_cost || 'N/A'}
                  </div>
                  <button
                    className="button confirm-button"
                    onClick={() => handleVisitNow(loc)}
                  >
                    Visit Now
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Booking Modal */}
        {selectedLocation && (
          <div className="booking-overlay">
            <div className="booking-form">
              <h2>Book Visit to {selectedLocation.location_name}</h2>
              
              <div className="form-group">
                <label htmlFor="travel-date">Travel Date</label>
                <input
                  id="travel-date"
                  className="form-input"
                  type="date"
                  value={travelDate}
                  onChange={(e) => setTravelDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>

              <div className="form-group">
                <label htmlFor="people-count">Number of People</label>
                <input
                  id="people-count"
                  className="form-input"
                  type="number"
                  min="1"
                  value={numberOfPeople}
                  onChange={(e) => setNumberOfPeople(e.target.value)}
                />
              </div>

              <div className="booking-actions">
                <button className="confirm-button" onClick={handleConfirmVisit}>
                  Confirm Booking
                </button>
                <button className="cancel-button" onClick={() => setSelectedLocation(null)}>
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

export default Locations;
