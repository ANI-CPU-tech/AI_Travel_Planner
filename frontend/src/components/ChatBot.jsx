import React, { useState, useRef, useEffect } from "react";
import Navbar from "../components/Navbar";
import API from "../api";
import '../styles/chatbot.css';

function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [locationCard, setLocationCard] = useState(null);
  const [planPreview, setPlanPreview] = useState(null);
  const chatEndRef = useRef(null);

  // Auto-scroll when new message arrives
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, locationCard]);

  // 🧠 Handle send message
  const handleSendMessage = async () => {
    if (!userInput.trim()) return;
    const message = userInput.trim();

    // Add user's message to the UI
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setUserInput("");
    setLoading(true);
    setLocationCard(null);
    // If the user explicitly asked for a plan, skip classify and call planner/generate
    const lowerEarly = message.toLowerCase();
    if (lowerEarly.includes('plan') || lowerEarly.includes('itinerary') || lowerEarly.includes('create a plan') || lowerEarly.includes('create plan')) {
      // show a temporary assistant message and generate plan
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Generating plan preview…' }]);
      try {
        await handleGeneratePlan(message);
      } finally {
        setLoading(false);
      }
      return;
    }

    try {
      // 🧩 Send message to your backend classify endpoint
      // Try with axios (will include auth header if tokens exist). If that returns 401 (e.g. invalid/expired tokens),
      // retry using a plain fetch POST without Authorization so anonymous users still get classification/fallback.
      let response;
      try {
        response = await API.post("/assistant/classify/", { message });
      } catch (err) {
        // if 401, retry anonymously
        if (err.response && err.response.status === 401) {
          try {
            const url = (API.defaults && API.defaults.baseURL ? API.defaults.baseURL.replace(/\/$/, '') : 'http://localhost:8000/api') + '/assistant/classify/';
            const res = await fetch(url, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ message }),
            });
            const json = await res.json();
            response = { data: json };
          } catch (fetchErr) {
            throw fetchErr;
          }
        } else {
          throw err;
        }
      }
      const data = response.data || {};

  // Prefer parsed classification / fallback. The backend now returns an enriched response
  // with keys like `gemini_classification`, `matching_locations`, `matching_homes`.
  const classification = data.gemini_classification || data.fallback || data;

      // Build a short human-friendly summary
      let summary = "I couldn't understand that.";
      // If the model returned raw_text that looks like JSON (e.g. plan JSON), try to parse it
      if (!classification.primary_destination && classification.raw_text && typeof classification.raw_text === 'string') {
        const raw = classification.raw_text.trim();
        if (raw.startsWith('{') || raw.includes('"summary"')) {
          try {
            const parsedRaw = JSON.parse(raw);
            if (parsedRaw && parsedRaw.summary) {
              summary = parsedRaw.summary;
            }
          } catch (e) {
            // ignore parse errors and fall back to raw_text substring
            summary = raw.substring(0, 400);
          }
        }
      }

      if (classification.primary_destination) {
        const pd = classification.primary_destination;
        const loc = pd.location || pd.name || "Unknown";
        const desc = pd.description || pd.region || "";
        const interests = Array.isArray(pd.interests) && pd.interests.length ? ` Interests: ${pd.interests.join(", ")}.` : "";
        summary = `${loc}${desc ? " — " + desc : ""}${interests}`;
      } else if (classification.raw_text) {
        // fallback to raw text
        // only show plain raw text if it isn't JSON-like (handled above)
        if (!summary || summary === "I couldn't understand that.") {
          summary = classification.raw_text.substring(0, 400);
        }
      } else if (data.error) {
        summary = data.error;
      }

      setMessages((prev) => [...prev.filter(m => !(m.role === 'assistant' && m.content === 'Generating plan preview…')), { role: "assistant", content: summary }]);

  // clear any previous plan preview when a new chat reply arrives
  setPlanPreview(null);

      // If the user's message explicitly asked for a plan, generate it automatically
      const lower = message.toLowerCase();
      if (lower.includes('plan') || lower.includes('itinerary') || lower.includes('create a plan') || lower.includes('create plan')) {
        // generate using the original message text
        handleGeneratePlan(message);
      }

      // If we have a primary destination, fetch richer search results (locations/homes)
      const resolveImageUrl = (img) => {
        if (!img) return null;
        try {
          // sometimes the field is a JSON string/object containing url/path
          if (typeof img === "string" && img.trim().startsWith('{')) {
            try {
              const parsed = JSON.parse(img);
              img = parsed.url || parsed.path || parsed.image || parsed.src || img;
            } catch (e) {
              // leave as-is
            }
          }

          if (typeof img === 'object' && img !== null) {
            img = img.url || img.path || img.image || img.src || null;
          }

          if (!img) return null;

          if (/^https?:\/\//i.test(img)) return img;
          const apiBase = (API.defaults && API.defaults.baseURL) || "http://localhost:8000/api";
          const backendBase = apiBase.replace(/\/api\/?$/, "");
          // ensure leading slash
          const path = img.startsWith("/") ? img : `/${img}`;
          return backendBase + path;
        } catch (e) {
          return null;
        }
      };
    // The classify endpoint returns enriched search results (matching_locations / matching_homes)
    const body = data || {};
        // prefer Location records, then Homes
        const firstLocation = (body.matching_locations && body.matching_locations[0]) || null;
        if (firstLocation) {
          // prefer serializer-provided absolute url
          const rawImg = firstLocation.image_url || firstLocation.location_image || firstLocation.location_image_url || null;
          const img = rawImg && typeof rawImg === 'object' ? (rawImg.url || rawImg.path || null) : rawImg;
          const imgResolved = resolveImageUrl(img);
          console.debug('Resolved location image:', { rawImg, img, imgResolved, firstLocation });
          setLocationCard({
            name: firstLocation.location_name || firstLocation.city || (classification.primary_destination && classification.primary_destination.location) || "",
            description: (firstLocation.description || "").slice(0, 200),
            image: imgResolved,
            price: firstLocation.average_cost || firstLocation.avg_cost || null,
            rating: firstLocation.rating || null,
          });
        } else if (body.matching_homes && body.matching_homes.length) {
          const firstHome = body.matching_homes[0];
          const rawImg = firstHome.image_url || firstHome.location_image || firstHome.location_image_url || null;
          const img = rawImg && typeof rawImg === 'object' ? (rawImg.url || rawImg.path || null) : rawImg;
          const imgResolved = resolveImageUrl(img);
          console.debug('Resolved home image:', { rawImg, img, imgResolved, firstHome });
          setLocationCard({
            name: firstHome.location_name || firstHome.city || (classification.primary_destination && classification.primary_destination.location) || "",
            description: (firstHome.description || "").slice(0, 200),
            image: imgResolved,
            price: firstHome.average_cost || null,
            rating: firstHome.rating || null,
          });
        }
        else {
          // No DB/scraped results — build a lightweight card from the classification itself
          try {
            const pd = classification.primary_destination || (classification.raw_text ? { location: classification.raw_text } : null);
            if (pd && (pd.location || pd.name)) {
              const name = pd.location || pd.name;
              const desc = pd.description || pd.region || (pd.interests ? `Interests: ${pd.interests.join(', ')}` : '');
              // Use Unsplash source to provide a representative image by query (falls back gracefully)
              const img = `https://source.unsplash.com/featured/?${encodeURIComponent(name)}`;
              console.debug('Synthetic card image:', { name, desc, img });
              setLocationCard({
                name: name,
                description: (desc || '').slice(0, 240),
                image: img,
                price: null,
                rating: null,
                synthetic: true,
              });
            }
          } catch (e) {
            // ignore — UI will just not show a card
          }
        }

      // end of classify flow
    } catch (error) {
      console.error("Error fetching chatbot response:", error);
      const errorMsg = error.response?.data?.error || "⚠️ Failed to get response from AI.";
      setMessages((prev) => [...prev, { role: "assistant", content: errorMsg }]);
    } finally {
      setLoading(false);
    }
  };

  // Generate a plan using the planner/generate endpoint (anonymous fallback supported)
  const handleGeneratePlan = async (text) => {
    const prompt = (text || userInput || '').trim();
    if (!prompt) return;
    setLoading(true);
    setPlanPreview(null);
    try {
      let response;
      try {
        response = await API.post('/planner/plans/generate/', { message: prompt });
      } catch (err) {
        // try anonymous fetch fallback in case of 401
        if (err.response && err.response.status === 401) {
          const url = (API.defaults && API.defaults.baseURL ? API.defaults.baseURL.replace(/\/$/, '') : 'http://localhost:8000/api') + '/planner/plans/generate/';
          const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: prompt }),
          });
          const json = await res.json();
          response = { data: json };
        } else {
          throw err;
        }
      }

      const data = response.data || {};
      if (data.error) {
        setMessages((prev) => [...prev, { role: 'assistant', content: data.error }]);
        return;
      }
      // If the backend returned raw_text (stringified JSON), try to parse it here
      if (data.raw_text && typeof data.raw_text === 'string') {
        const raw = data.raw_text.trim();
        let parsed = null;
        try {
          parsed = JSON.parse(raw);
        } catch (e) {
          try {
            const first = raw.indexOf('{');
            const last = raw.lastIndexOf('}');
            if (first !== -1 && last !== -1 && last > first) {
              parsed = JSON.parse(raw.slice(first, last + 1));
            }
          } catch (e2) {
            try {
              const m = raw.match(/(\{[\s\S]*\})/);
              if (m) parsed = JSON.parse(m[1]);
            } catch (e3) {
              parsed = null;
            }
          }
        }

        if (parsed) {
          setPlanPreview(parsed);
        } else {
          // couldn't parse, show a friendly error instead of dumping raw JSON
          setMessages((prev) => [...prev, { role: 'assistant', content: 'Generated plan could not be parsed. Showing raw preview.' }]);
          setPlanPreview(data);
        }
      } else {
        // store preview
        setPlanPreview(data);
      }
    } catch (e) {
      console.error('Plan generation failed', e);
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Failed to generate plan.' }]);
    } finally {
      setLoading(false);
    }
  };

  // Save the currently previewed plan (requires auth)
  const handleSavePlan = async () => {
    if (!planPreview) return;
    setLoading(true);
    try {
      const title = planPreview.summary ? planPreview.summary.substring(0, 80) : '';
      const itinerary = planPreview;
      const start_date = planPreview.start_date || null;
      const end_date = planPreview.end_date || null;
      const num_days = Array.isArray(planPreview.itinerary) ? planPreview.itinerary.length : (planPreview.itinerary ? planPreview.itinerary.length : null);

      const payload = { title, start_date, end_date, num_days, summary: planPreview.summary || '', itinerary };

      await API.post('/planner/plans/', payload);
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Plan saved to your account.' }]);
      // Optionally clear preview
      setPlanPreview(null);
    } catch (err) {
      console.error('Save plan failed', err);
      if (err.response && err.response.status === 401) {
        setMessages((prev) => [...prev, { role: 'assistant', content: 'Please login to save plans.' }]);
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: 'Failed to save plan.' }]);
      }
    } finally {
      setLoading(false);
    }
  };

  // Press Enter to send
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div>
      <Navbar />
      <div className="chatbot-container">
        <header className="chatbot-header">
          <h1>AI Travel Assistant</h1>
          <p>Ask me about destinations, plan trips, or get travel recommendations!</p>
        </header>

        <div className="chat-window">
          {messages.length === 0 && (
            <div className="chat-welcome">
              <h3>Welcome to your AI Travel Assistant! 👋</h3>
              <p>Try asking about destinations, planning trips, or get travel recommendations.</p>
              <p>Example: "Tell me about interesting places to visit in Tokyo"</p>
            </div>
          )}

          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === "user" ? "👤" : "🤖"}
              </div>
              <div className="message-content">
                {msg.content}
              </div>
            </div>
          ))}

          {/* Location card */}
          {locationCard && (
            <div className="location-card">
              <div className="location-image">
                {locationCard.image ? (
                  <img
                    src={locationCard.image}
                    alt={locationCard.name}
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = `https://source.unsplash.com/featured/?${encodeURIComponent(locationCard.name || 'travel')}`;
                    }}
                  />
                ) : (
                  <div className="no-image">No image</div>
                )}
              </div>
              <div className="location-details">
                <h3 className="location-title">{locationCard.name}</h3>
                <div className="location-meta">
                  {locationCard.price && (
                    <span>
                      <i className="fas fa-tag"></i>
                      Avg cost: {typeof locationCard.price === 'number' ? locationCard.price.toLocaleString() : locationCard.price}
                    </span>
                  )}
                  {locationCard.rating && (
                    <span>
                      <i className="fas fa-star"></i>
                      Rating: {locationCard.rating}
                    </span>
                  )}
                </div>
                <p className="location-description">{locationCard.description}</p>
              </div>
            </div>
          )}

          {/* Plan preview card */}
          {planPreview && (
            <div className="plan-preview">
              <div className="plan-header">
                <h3>{planPreview.summary || 'Your Travel Plan'}</h3>
                {planPreview.start_date && planPreview.end_date && (
                  <div className="plan-dates">
                    <i className="fas fa-calendar-alt"></i>
                    {planPreview.start_date} → {planPreview.end_date}
                  </div>
                )}
              </div>
              <div className="plan-content">
                {Array.isArray(planPreview.itinerary) ? (
                  planPreview.itinerary.map((day, idx) => (
                    <div key={idx} className="plan-day">
                      <div className="plan-day-header">
                        Day {day.day || idx + 1} {day.date && `— ${day.date}`}
                      </div>
                      <ul className="plan-activities">
                        {(day.activities || []).map((act, i) => (
                          <li key={i}>
                            {act.type && <b>{act.type}: </b>}
                            {act.name} 
                            {act.description && <span> — {act.description}</span>}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))
                ) : (
                  <pre>{JSON.stringify(planPreview, null, 2)}</pre>
                )}
              </div>
              <div className="plan-actions">
                <button 
                  className="send-button" 
                  onClick={handleSavePlan} 
                  disabled={loading}
                >
                  <i className="fas fa-save"></i>
                  Save Plan
                </button>
                <button 
                  className="send-button" 
                  onClick={() => setPlanPreview(null)}
                  style={{ background: 'var(--gray-500)' }}
                >
                  Close
                </button>
              </div>
            </div>
          )}

          <div ref={chatEndRef}></div>
        </div>

        <div className="chat-input-container">
          <textarea
            className="chat-input"
            rows="2"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about destinations, plan a trip, or get travel recommendations..."
          />
          <button 
            className="send-button" 
            onClick={handleSendMessage} 
            disabled={loading}
          >
            {loading ? (
              <>
                <i className="fas fa-spinner fa-spin"></i>
                Processing...
              </>
            ) : (
              <>
                <i className="fas fa-paper-plane"></i>
                Send
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Chatbot;
