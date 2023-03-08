var clickmarker;
const form = document.getElementById("submit-recommendation")
mapboxgl.accessToken = 'pk.eyJ1IjoianNhbnRpYWdvLXByb2JlbHRlIiwiYSI6ImNsZThrajZuMTBnOHgzb25ic3NjcjE2dWEifQ.m26LzPlEAYHiIyIKtXV6QQ';

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/satellite-streets-v11',
    center: [longitude, latitude],
    zoom: 12
});

map.on('load', () => {
    map.addSource('wms-test-source', {
        'type': 'raster',
        'tiles': [
        'https://wms.mapa.gob.es/sigpac/ows?service=WMS&request=GetMap&layers=sigpac%3Arecinto&styles=&format=image%2Fpng&transparent=true&version=1.3.0&wmtver=1.3.0&width=256&height=256&crs=EPSG%3A3857&bbox={bbox-epsg-3857}'
    ],
    'tileSize': 256
    });
    map.addLayer(
        {
            'id': 'wms-test-layer',
            'type': 'raster',
            'source': 'wms-test-source',
            'paint': {}
        }
    );
});

/* Given a query in the form "lng, lat" or "lat, lng"
* returns the matching geographic coordinate(s)
* as search results in carmen geojson format,
* https://github.com/mapbox/carmen/blob/master/carmen-geojson.md */
const coordinatesGeocoder = function (query) {
    // Match anything which looks like
    // decimal degrees coordinate pair.
    const matches = query.match(
    /^[ ]*(?:Lat: )?(-?\d+\.?\d*)[, ]+(?:Lng: )?(-?\d+\.?\d*)[ ]*$/i
    );
    if (!matches) {
    return null;
    }
     
    function coordinateFeature(lng, lat) {
    return {
    center: [lng, lat],
    geometry: {
    type: 'Point',
    coordinates: [lng, lat]
    },
    place_name: 'Lat: ' + lat + ' Lng: ' + lng,
    place_type: ['coordinate'],
    properties: {},
    type: 'Feature'
    };
    }
     
    const coord1 = Number(matches[1]);
    const coord2 = Number(matches[2]);
    const geocodes = [];
     
    if (coord1 < -90 || coord1 > 90) {
    // must be lng, lat
    geocodes.push(coordinateFeature(coord1, coord2));
    }
     
    if (coord2 < -90 || coord2 > 90) {
    // must be lat, lng
    geocodes.push(coordinateFeature(coord2, coord1));
    }
     
    if (geocodes.length === 0) {
    // else could be either lng, lat or lat, lng
    geocodes.push(coordinateFeature(coord1, coord2));
    geocodes.push(coordinateFeature(coord2, coord1));
    }
     
    return geocodes;
    };

var latlongContainer = $('#latlong')
if (latlongContainer.length>0) {
// Add the control to the map.
    map.addControl(
        new MapboxGeocoder({
        accessToken: mapboxgl.accessToken,
        localGeocoder: coordinatesGeocoder,
        zoom: 4,
        placeholder: 'Search location',
        mapboxgl: mapboxgl,
        reverseGeocode: true
        })
        );
}

var show_maker = $('#show_marker')
if (show_maker.length>0) {
    const marker1 = new mapboxgl.Marker()
    .setLngLat([longitude, latitude])
    .addTo(map);
}

map.on('click', (e) => {
    // Copy coordinates array.
    const coordinates = e.lngLat;
    console.log(coordinates)

    if (!clickmarker) {
        clickmarker = new mapboxgl.Marker()
        .setLngLat(coordinates)
        .addTo(map);
        form.append("latitude", coordinates[0])
        form.append("longitude", coordinates[1])
    } else {
        form.setAttribute("latitude", coordinates[0])
        form.setAttribute("longitude", coordinates[1])
        clickmarker.setLngLat(coordinates)
    }

});