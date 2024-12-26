document.addEventListener('DOMContentLoaded', () => {
    let map;
    let routeLayer;

    document.getElementById('travel-form').addEventListener('submit', async (event) => {
        event.preventDefault();

        const start = document.getElementById('start').value;
        const destination = document.getElementById('destination').value;
        const preferences = document.getElementById('preferences').value;
        const transportMode = document.getElementById('transport-mode').value;
        const loadingSpinner = document.getElementById('Loading');
        loadingSpinner.style.display = 'inline-block';

        try {
            const response = await fetch('/find_route', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ start, destination, preferences, transportMode })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Backend Response:", data);

            if (data.error) {
                alert(data.error);
                return;
            }

            displayRouteDetails(data);
            displayEmissionChart(data.emissions);
            displayMap(data.route);
        } catch (error) {
            console.error("Error fetching route data:", error);
            alert("An error occurred while fetching route data. Please try again.");
        } finally {
            loadingSpinner.style.display = 'none';
        }
    });
    

    function displayRouteDetails(data) {
        const details = document.getElementById('route-details');
        details.innerHTML = `
            <p><strong>Start:</strong> ${data.start}</p>
            <p><strong>Destination:</strong> ${data.destination}</p>
            <p><strong>Travel Mode:</strong> ${data.mode}</p>
            <p><strong>Distance:</strong> ${data.distance} km</p>
            <p><strong>Estimated Emissions:</strong> ${data.emissions[data.mode]} g CO₂</p>
        `;
    }

    function displayEmissionChart(emissions) {
        const canvas = document.getElementById('emissions-chart');
        const ctx = canvas.getContext('2d');

        const filteredEmissions = Object.entries(emissions).filter(([key, value]) => {
            return key !== 'walking' && key !== 'cycling';
        });
    
        const labels = filteredEmissions.map(entry => entry[0]);
        const data = filteredEmissions.map(entry => entry[1]);

        canvas.height = 250;
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'CO₂ Emissions (grams per km)',
                    data: data,
                    backgroundColor: ['#2d6a4f', '#52b788']
                }]
            }
        });
    }

    function displayMap(route) {
        const mapContainer = document.getElementById('map-container');
        mapContainer.style.display = 'block';

        const map = L.map('map').setView([12.9716, 77.5946], 10); 

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        if (!route || !route.coordinates || route.coordinates.length === 0) {
            console.error("Invalid route data:", route);
            alert("Could not display the map due to invalid route data.");
            return;
        }

        const latlngs = route.coordinates.map(coord => [coord[1], coord[0]]);
        const polyline = L.polyline(latlngs, { color: 'blue' }).addTo(map);

        map.fitBounds(polyline.getBounds());
    }
});
