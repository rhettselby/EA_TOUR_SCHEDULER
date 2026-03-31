import { useState, useEffect } from "react";

const STATUS_CONFIG = {
  unassigned: { label: "Unassigned", color: "#c53030", bg: "#fff5f5", border: "#fc8181", light: "#fed7d7" },
  message_sent: { label: "Message Sent", color: "#b7791f", bg: "#fffff0", border: "#ecc94b", light: "#fefcbf" },
  confirmed: { label: "Confirmed", color: "#276749", bg: "#f0fff4", border: "#48bb78", light: "#c6f6d5" },
  past_event: { label: "Past Event", color: "#2d3748", bg: "#f7fafc", border: "#718096", light: "#e2e8f0" },
};

// --- Timezone-safe date utilities ---

function formatTime(dt) {
  const d = new Date(dt);
  return d.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZone: "America/Los_Angeles",
  });
}

function formatDayHeader(dateStr) {
  // dateStr is a UTC date key "YYYY-MM-DD", display in PST
  const d = new Date(dateStr + "T00:00:00Z");
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    timeZone: "America/Los_Angeles",
  });
}

function getWeekLabel(weekStartStr) {
  const d = new Date(weekStartStr + "T00:00:00Z");
  const weekEnd = new Date(d);
  weekEnd.setUTCDate(d.getUTCDate() + 6);
  const fmt = (x) =>
    x.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "America/Los_Angeles",
    });
  return { short: `${fmt(d)} – ${fmt(weekEnd)}` };
}

// Bucket by UTC date to avoid timezone-shifting tours into wrong day
function getDateKey(dt) {
  const d = new Date(dt);
  return d.toISOString().slice(0, 10); // "YYYY-MM-DD" always UTC
}

// Week starts on Monday to match Django backend
function getWeekKey(dt) {
  const d = new Date(dt);
  const day = d.getUTCDay(); // 0 = Sunday
  const diff = day === 0 ? 6 : day - 1; // Monday = 0
  const weekStart = new Date(d);
  weekStart.setUTCDate(d.getUTCDate() - diff);
  weekStart.setUTCHours(0, 0, 0, 0);
  return weekStart.toISOString().slice(0, 10);
}

// Group tours with the same start_dt into one combined card
function groupByStartTime(tours) {
  const groups = {};
  tours.forEach((tour) => {
    const key = tour.start_dt;
    if (!groups[key]) {
      groups[key] = { ...tour, guests: [] };
    }
    // Collect guest names from all tours at this time
    if (tour.guest_name && !groups[key].guests.includes(tour.guest_name)) {
      groups[key].guests.push(tour.guest_name);
    }
    // Sum guest counts
    if (groups[key].id !== tour.id) {
      groups[key].number_of_guests += tour.number_of_guests;
    }
  });
  return Object.values(groups).sort((a, b) => new Date(a.start_dt) - new Date(b.start_dt));
}

// --- Components ---

function TourCard({ tour, onStatusChange }) {
  const [updating, setUpdating] = useState(false);
  const status = STATUS_CONFIG[tour.status] || STATUS_CONFIG.unassigned;

  const handleStatus = async (newStatus) => {
    setUpdating(true);
    try {
      await fetch(`/api/tours/${tour.id}/update_status/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      onStatusChange(tour.id, newStatus);
    } catch (e) {
      console.error("Failed to update status", e);
    }
    setUpdating(false);
  };

  const guestList = tour.guests && tour.guests.length > 0 ? tour.guests : [tour.guest_name || "Guest"];
  const isGrouped = guestList.length > 1;

  return (
    <div style={{
      background: status.light,
      border: `2px solid ${status.border}`,
      borderRadius: "10px",
      padding: "16px 20px",
      marginBottom: "10px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
      opacity: updating ? 0.6 : 1,
      transition: "opacity 0.2s",
    }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: "20px", flex: 1 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "13px", color: status.color, fontFamily: "'DM Mono', monospace", letterSpacing: "0.05em", fontWeight: "600" }}>
            {formatTime(tour.start_dt)}
          </div>

          {/* Guest names — stacked if multiple */}
          {isGrouped ? (
            <div style={{ marginTop: "4px" }}>
              {guestList.map((name, idx) => (
                <div key={idx} style={{
                  fontSize: "15px",
                  fontWeight: idx === 0 ? "600" : "400",
                  color: idx === 0 ? "#1a202c" : "#4a5568",
                  fontFamily: "'Playfair Display', serif",
                  lineHeight: "1.4",
                }}>
                  {name}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: "16px", fontWeight: "600", color: "#1a202c", marginTop: "2px", fontFamily: "'Playfair Display', serif" }}>
              {guestList[0]}
            </div>
          )}

          <div style={{ display: "flex", gap: "8px", marginTop: "6px", alignItems: "center", flexWrap: "wrap" }}>
            <span style={{ fontSize: "12px", color: "#4a5568", background: "rgba(255,255,255,0.7)", border: "1px solid rgba(0,0,0,0.08)", borderRadius: "4px", padding: "2px 8px" }}>
              {tour.number_of_guests} {tour.number_of_guests === 1 ? "guest" : "guests"}
            </span>
            {isGrouped && (
              <span style={{ fontSize: "12px", color: "#2b6cb0", background: "rgba(255,255,255,0.7)", border: "1px solid #90cdf4", borderRadius: "4px", padding: "2px 8px" }}>
                {guestList.length} groups
              </span>
            )}
            {tour.group_tour && (
              <span style={{ fontSize: "12px", color: "#553c9a", background: "rgba(255,255,255,0.7)", border: "1px solid #d6bcfa", borderRadius: "4px", padding: "2px 8px" }}>
                Group Tour
              </span>
            )}
            <span style={{ fontSize: "12px", color: status.color, background: "rgba(255,255,255,0.7)", border: `1px solid ${status.border}`, borderRadius: "4px", padding: "2px 8px", fontWeight: "600" }}>
              {status.label}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "8px", alignItems: "center", flexShrink: 0, marginLeft: "16px" }}>
        {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
          <button
            key={key}
            onClick={() => handleStatus(key)}
            disabled={updating || tour.status === key}
            title={cfg.label}
            style={{
              width: "30px", height: "30px", borderRadius: "50%",
              border: tour.status === key ? `3px solid #1a202c` : `2px solid ${cfg.border}`,
              background: cfg.border, cursor: tour.status === key ? "default" : "pointer",
              opacity: tour.status === key ? 1 : 0.5,
              transition: "opacity 0.15s, transform 0.15s", outline: "none",
              transform: tour.status === key ? "scale(1.2)" : "scale(1)",
            }}
          />
        ))}
      </div>
    </div>
  );
}

function CircleArrowButton({ onClick, disabled, direction }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: "36px", height: "36px", borderRadius: "50%",
        border: `2px solid ${disabled ? "#e2e8f0" : hovered ? "#94a3b8" : "#cbd5e0"}`,
        background: disabled ? "transparent" : hovered ? "#f1f5f9" : "#fff",
        color: disabled ? "#cbd5e0" : "#0f172a",
        fontSize: "18px", fontWeight: "600",
        display: "flex", alignItems: "center", justifyContent: "center",
        cursor: disabled ? "default" : "pointer",
        transition: "all 0.15s",
        outline: "none", flexShrink: 0,
        lineHeight: 1,
      }}
    >
      {direction === "left" ? "‹" : "›"}
    </button>
  );
}

// --- Main App ---

export default function App() {
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeWeekIdx, setActiveWeekIdx] = useState(0);
  const [scraping, setScraping] = useState(false);
  const [scrapeMessage, setScrapeMessage] = useState(null);
  const [initialWeekSet, setInitialWeekSet] = useState(false);

  useEffect(() => {
    fetch("/api/tours/")
      .then((r) => r.json())
      .then((data) => { setTours(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const handleStatusChange = (id, newStatus) => {
    setTours((prev) => prev.map((t) => t.id === id ? { ...t, status: newStatus } : t));
  };

  const handleLoadTours = async () => {
    setScraping(true);
    setScrapeMessage(null);
    try {
      const res = await fetch("/api/tours/scrape/", { method: "POST" });
      const data = await res.json();
      if (res.status === 429) {
        setScrapeMessage({ type: "warning", text: data.message });
      } else {
        setScrapeMessage({ type: "success", text: "Scraper triggered! New tours will appear shortly." });
      }
    } catch (e) {
      setScrapeMessage({ type: "error", text: "Failed to trigger scraper." });
    }
    setScraping(false);
    setTimeout(() => setScrapeMessage(null), 4000);
  };

  // Group tours into weeks -> days
  const grouped = {};
  tours.forEach((tour) => {
    const wk = getWeekKey(tour.start_dt);
    const dk = getDateKey(tour.start_dt);
    if (!grouped[wk]) grouped[wk] = {};
    if (!grouped[wk][dk]) grouped[wk][dk] = [];
    grouped[wk][dk].push(tour);
  });

  const weekKeys = Object.keys(grouped).sort();
  const activeWeek = weekKeys[activeWeekIdx];
  const activeWeekDays = activeWeek ? grouped[activeWeek] : {};

  const todayTours = tours.filter(t => getDateKey(t.start_dt) === todayKey);
  const totalToday = groupByStartTime(todayTours).length;

  useEffect(() => {
    if (!loading && !initialWeekSet && weekKeys.length > 0) {
      const todayWk = getWeekKey(new Date());
      const idx = weekKeys.indexOf(todayWk);
      setActiveWeekIdx(idx >= 0 ? idx : 0);
      setInitialWeekSet(true);
    }
  }, [loading, weekKeys.length]);

  const getWeekStats = (weekKey) => {
  const days = grouped[weekKey] || {};
  // apply same grouping logic so multi-guest same-time tours count as 1
  const allGrouped = Object.values(days).flatMap((dayTours) => groupByStartTime(dayTours));
  return {
    total: allGrouped.length,
    needAttention: allGrouped.filter(t => t.status === "unassigned").length,
    confirmed: allGrouped.filter(t => t.status === "confirmed").length,
  };
};

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "'DM Sans', sans-serif", background: "#f8fafc" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Playfair+Display:wght@600;700&family=DM+Mono&display=swap" rel="stylesheet" />

      {/* Sidebar */}
      <div style={{ width: "240px", minWidth: "240px", background: "#0f172a", color: "#e2e8f0", display: "flex", flexDirection: "column", padding: "32px 0" }}>
        <div style={{ padding: "0 24px 32px", borderBottom: "1px solid #1e293b" }}>
          <div style={{ fontSize: "11px", letterSpacing: "0.15em", color: "#64748b", textTransform: "uppercase", marginBottom: "6px" }}>EA Tours</div>
          <div style={{ fontSize: "22px", fontWeight: "700", fontFamily: "'Playfair Display', serif", color: "#f1f5f9" }}>Scheduler</div>
        </div>

        <nav style={{ padding: "24px 16px", flex: 1 }}>
          {[
            { label: "Tour Schedule", icon: "📅", active: true },
            { label: "AI Agent", icon: "🤖", active: false, soon: true },
          ].map((item) => (
            <div key={item.label} style={{
              display: "flex", alignItems: "center", gap: "10px",
              padding: "10px 12px", borderRadius: "6px", marginBottom: "4px",
              background: item.active ? "#1e293b" : "transparent",
              color: item.active ? "#f1f5f9" : "#64748b",
              cursor: item.soon ? "default" : "pointer",
              fontSize: "14px", fontWeight: "500",
            }}>
              <span>{item.icon}</span>
              {item.label}
              {item.soon && <span style={{ marginLeft: "auto", fontSize: "10px", color: "#475569", background: "#1e293b", padding: "2px 6px", borderRadius: "4px" }}>Soon</span>}
            </div>
          ))}

          <div style={{ marginTop: "8px", padding: "0 4px" }}>
            <button
              onClick={handleLoadTours}
              disabled={scraping}
              style={{
                width: "100%", padding: "10px 12px", borderRadius: "6px",
                background: scraping ? "#1e293b" : "#1e3a5f",
                border: "1px solid #2d5a8e", color: scraping ? "#64748b" : "#93c5fd",
                fontSize: "14px", fontWeight: "500", cursor: scraping ? "default" : "pointer",
                display: "flex", alignItems: "center", gap: "10px",
                transition: "background 0.2s",
              }}
            >
              <span>{scraping ? "⏳" : "🔄"}</span>
              {scraping ? "Loading..." : "Load New Tours"}
            </button>
            <div style={{ fontSize: "11px", color: "#475569", marginTop: "6px", padding: "0 4px", lineHeight: "1.4" }}>
              ⚠️ Use sparingly — high memory usage
            </div>
            {scrapeMessage && (
              <div style={{
                marginTop: "8px", padding: "8px 10px", borderRadius: "6px", fontSize: "12px",
                background: scrapeMessage.type === "success" ? "#052e16" : scrapeMessage.type === "warning" ? "#2d1f00" : "#2d0a0a",
                color: scrapeMessage.type === "success" ? "#86efac" : scrapeMessage.type === "warning" ? "#fcd34d" : "#fca5a5",
                border: `1px solid ${scrapeMessage.type === "success" ? "#166534" : scrapeMessage.type === "warning" ? "#854d0e" : "#7f1d1d"}`,
              }}>
                {scrapeMessage.text}
              </div>
            )}
          </div>
        </nav>

        <div style={{ padding: "24px", borderTop: "1px solid #1e293b" }}>
          <div style={{ fontSize: "11px", letterSpacing: "0.1em", color: "#475569", textTransform: "uppercase", marginBottom: "12px" }}>Status</div>
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
            <div key={key} style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: cfg.border }} />
              <span style={{ fontSize: "13px", color: "#94a3b8" }}>{cfg.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, padding: "40px 48px", overflowY: "auto" }}>
        <div style={{ maxWidth: "860px" }}>

          {/* Header */}
          <div style={{ marginBottom: "32px", display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
            <div>
              <h1 style={{ fontSize: "28px", fontWeight: "700", fontFamily: "'Playfair Display', serif", color: "#0f172a", margin: 0 }}>Tour Schedule</h1>
              <p style={{ color: "#64748b", marginTop: "4px", fontSize: "14px", margin: "4px 0 0" }}>
                {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric", timeZone: "America/Los_Angeles" })}
              </p>
            </div>
            {!loading && (
              <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "10px 18px", textAlign: "center", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
                <div style={{ fontSize: "22px", fontWeight: "700", color: "#3b82f6", fontFamily: "'Playfair Display', serif", lineHeight: 1 }}>{totalToday}</div>
                <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "3px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Tours Today</div>
              </div>
            )}
          </div>

          {/* Week navigator */}
          {!loading && weekKeys.length > 0 && (() => {
            const { total: weekTourCount, needAttention: weekNeedAttention, confirmed: weekConfirmed } = getWeekStats(activeWeek);
            const canPrev = activeWeekIdx > 0;
            const canNext = activeWeekIdx < weekKeys.length - 1;
            return (
              <div style={{ marginBottom: "32px", background: "#fff", border: "1px solid #e2e8f0", borderRadius: "10px", boxShadow: "0 1px 3px rgba(0,0,0,0.04)", padding: "16px 20px", display: "flex", alignItems: "center", gap: "16px" }}>
                <CircleArrowButton onClick={() => setActiveWeekIdx(i => Math.max(0, i - 1))} disabled={!canPrev} direction="left" />
                <div style={{ flex: 1, textAlign: "center" }}>
                  <div style={{ fontSize: "20px", fontWeight: "700", fontFamily: "'Playfair Display', serif", color: "#0f172a", marginBottom: "2px" }}>
                    Week {tours.find(t => getWeekKey(t.start_dt) === activeWeek)?.week_number ?? "—"}
                  </div>
                  <div style={{ fontSize: "13px", color: "#64748b", marginBottom: "6px" }}>{getWeekLabel(activeWeek).short}</div>
                  <div style={{ fontSize: "12px", display: "flex", justifyContent: "center", gap: "12px" }}>
                    <span style={{ color: "#3b82f6", fontWeight: "500" }}>{weekTourCount} {weekTourCount === 1 ? "tour" : "tours"}</span>
                    <span style={{ color: "#cbd5e0" }}>|</span>
                    <span style={{ color: "#22c55e", fontWeight: "500" }}>{weekConfirmed} confirmed</span>
                    <span style={{ color: "#cbd5e0" }}>|</span>
                    <span style={{ color: weekNeedAttention > 0 ? "#ef4444" : "#94a3b8", fontWeight: weekNeedAttention > 0 ? "600" : "400" }}>
                      {weekNeedAttention > 0 ? `⚠️ ${weekNeedAttention} need attention` : "✓ all assigned"}
                    </span>
                  </div>
                </div>
                <CircleArrowButton onClick={() => setActiveWeekIdx(i => Math.min(weekKeys.length - 1, i + 1))} disabled={!canNext} direction="right" />
              </div>
            );
          })()}

          {/* Tour list */}
          {loading ? (
            <div style={{ color: "#94a3b8", fontSize: "15px" }}>Loading tours...</div>
          ) : weekKeys.length === 0 ? (
            <div style={{ color: "#94a3b8", fontSize: "15px" }}>No upcoming tours found.</div>
          ) : (
            Object.keys(activeWeekDays).sort().map((dk) => {
              // Group tours at the same start time into one card
              const groupedByTime = groupByStartTime(activeWeekDays[dk]);
              return (
                <div key={dk} style={{ marginBottom: "28px" }}>
                  <div style={{ fontSize: "14px", fontWeight: "700", color: "#334155", marginBottom: "12px", display: "flex", alignItems: "center", gap: "10px" }}>
                    <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#3b82f6" }} />
                    {formatDayHeader(dk)}
                    <span style={{ fontSize: "12px", color: "#94a3b8", fontWeight: "400" }}>
                      {groupedByTime.length} {groupedByTime.length === 1 ? "tour" : "tours"}
                    </span>
                  </div>
                  {groupedByTime.map((tour) => (
                    <TourCard key={tour.id} tour={tour} onStatusChange={handleStatusChange} />
                  ))}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}