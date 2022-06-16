// Create a map object.
var myMap = L.map("map", {
    center: [39.74, -104.99],
    zoom: 10
});

// Add a tile layer.
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(myMap);

// Define a set of city markers
var littleton = L.marker([39.61, -105.02]).bindPopup('This is Littleton, CO.');
var denver = L.marker([39.74, -104.99]).bindPopup('This is Denver, CO.');
var aurora = L.marker([39.73, -104.8]).bindPopup('This is Aurora, CO.');
var golden = L.marker([39.77, -105.23]).bindPopup('This is Golden, CO.');

// Instead of each one to the map, we can use the LayerGroup:
L.layerGroup([littleton, denver, aurora, golden]).addTo(myMap);