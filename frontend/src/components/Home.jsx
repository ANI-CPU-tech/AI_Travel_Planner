import React, { useEffect, useState, useRef } from 'react';
import Navbar from '../components/Navbar';
import API from '../api';
import '../styles/common.css';
import '../styles/home.css';

function Home() {
  const [locations, setLocations] = useState([]);
  const [homes, setHomes] = useState([]);
  const [loading, setLoading] = useState(true);

  // Refs for scrolling
  const locationsRef = useRef(null);
  const hotelsRef = useRef(null);

  // Fetch both locations and homes
  const fetchData = async () => {
    try {
      const [locationsRes, homesRes] = await Promise.all([
        API.get('/locations/'),
        API.get('/homes/'),
      ]);
      setLocations(locationsRes.data);
      setHomes(homesRes.data);
    } catch (error) {
      console.error('Error fetching home data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Helper for image URLs
  const getImageUrl = (path) => {
    if (!path) return null;
    return path.startsWith('http')
      ? path
      : `http://localhost:8000/${
          path.startsWith('/') ? path.slice(1) : path
        }`;
  };

  // Scroll handlers
  const scrollToLocations = () => {
    locationsRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollToHotels = () => {
    hotelsRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div>
      <Navbar />

      {/* 🏝️ HERO SECTION */}
      <section className="hero">
        <div className="hero-content">
          <h1>Welcome to AI Travel Planner</h1>
          <p>
            Discover breathtaking destinations and plan your perfect stay —
            all with a touch of AI magic.
          </p>

          <div className="hero-buttons">
            <button className="button button-hero" onClick={scrollToLocations}>
              Explore Locations
            </button>
            <button className="button button-hero button-secondary" onClick={scrollToHotels}>
              Find Hotels
            </button>
          </div>
        </div>
      </section>

      {/* 🗺️ LOCATIONS SECTION */}
      <section ref={locationsRef} className="container">
        <h2 className="section-title">Featured Locations</h2>

        {loading ? (
          <div className="loading">Loading...</div>
        ) : (
          <div className="locations-grid">
            {locations.slice(0, 10).map((loc) => (
              <div key={loc.id} className="location-card">
                {loc.location_image && (
                  <div className="card-image-container">
                    <img
                      className="card-image"
                      src={getImageUrl(loc.location_image)}
                      alt={loc.location_name}
                      loading="lazy"
                      onError={(e) => {
                        e.target.src = 'https://images.unsplash.com/photo-1469474968028-56623f02e42e';
                        e.target.onerror = null;
                      }}
                    />
                  </div>
                )}
                <div className="card-content">
                  <h3 className="card-title">{loc.location_name}</h3>
                  <div className="card-info">
                    {loc.city}, {loc.country}
                  </div>
                  <div className="card-info">
                    {loc.category} • Best Time: {loc.best_time_to_visit || 'Anytime'}
                  </div>
                  <div className="card-rating">
                    ★ {loc.rating || 'N/A'}
                  </div>
                  <div className="card-price">
                    From ₹{loc.average_cost || 'N/A'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <hr />

      {/* 🏨 HOTELS SECTION */}
      <section ref={hotelsRef} className="container">
        <h2 className="section-title">Top-Rated Hotels</h2>

        {loading ? (
          <div className="loading">Loading...</div>
        ) : (
          <div className="hotels-grid">
            {homes.slice(0, 10).map((home) => (
              <div key={home.id} className="hotel-card">
                {home.location_image && (
                  <div className="card-image-wrapper">
                    <div className="card-image-container">
                      <img
                        className="card-image"
                        src={getImageUrl(home.location_image)}
                        alt={home.location_name}
                        loading="lazy"
                        onError={(e) => {
                          e.target.src = 'https://images.unsplash.com/photo-1566073771259-6a8506099945';
                          e.target.onerror = null;
                        }}
                      />
                    </div>
                    {home.category && (
                      <span className="card-badge">{home.category}</span>
                    )}
                  </div>
                )}
                <div className="card-content">
                  <h3 className="card-title">{home.location_name}</h3>
                  <div className="card-info">
                    <span className="card-location">
                      {home.city}, {home.country}
                    </span>
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
                  <div className="card-footer">
                    <div className="card-price">
                      <span className="price-label">From</span>
                      <span className="price-amount">₹{home.average_cost || 'N/A'}</span>
                      <span className="price-period">/night</span>
                    </div>
                    <button className="button button-secondary" onClick={() => navigate('/hotels')}>
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default Home;
