import { useState, useEffect } from "react";

function App() {
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/tours/")
      .then(res => res.json())
      .then(data => {
        setTours(data);
        setLoading(false);
      })
      .catch(err => console.error("Error fetching tours:", err));
  }, []);

  if (loading) return <p>Loading tours...</p>;

  return (
    <div>
      <h1>Upcoming Tours</h1>
      {tours.map(tour => (
        <div key={tour.id}>
          <p>{tour.guest_name}</p>
          <p>{tour.start_dt}</p>
          <p>{tour.end_dt}</p>
          <p>Guests: {tour.number_of_guests}</p>
          {tour.group_tour && <p>Group Tour</p>}
        </div>
      ))}
    </div>
  );
}

export default App;