'use strict'

var pointChoice
var map = null
var markers = []
var infowindows = []
var infowindowsOpened = null
var runningRequest = false
var heatmap = null
var heatMap = null
var heatMapPoints = []
var isHeatMap = false
var datasetData = []
var datasetOptions = JSON.parse(document.querySelector('#dataset_json').innerHTML)

function HeatMapControl(controlDiv, map) {
  var control = this;

  controlDiv.style.clear = 'both';

  var heatMapUI = document.createElement('div');
  heatMapUI.id = 'heatMapUI';
  controlDiv.appendChild(heatMapUI);

  var heatMapText = document.createElement('div');
  heatMapText.id = 'heatMapText';
  heatMapText.innerHTML = 'Heat';
  heatMapUI.appendChild(heatMapText);

  heatMapUI.addEventListener('click', function() {
    heatMapPoints = markers.map(function(marker) {
      marker.setVisible(isHeatMap);
      return marker.position;
    });

    isHeatMap = !isHeatMap;

    if (isHeatMap) {
      heatmap.setData(heatMapPoints);
      heatmap.setMap(map);
      heatMapText.innerHTML = 'Normal';
    } else {
      heatmap.setMap(null);
      heatMapText.innerHTML = 'Heat';
    }
    if (infowindowsOpened != null) {
      infowindowsOpened.close();
    }
  });
}

function initMap() {
  // Create a map object and specify the DOM element for display.
  var mapType = new google.maps.StyledMapType([{
    featureType: "all",
    elementType: "all",
    stylers: [{
      saturation: -100
    }]
  }], {
    name: "Grayscale"
  });

  map = new google.maps.Map(document.getElementById('map'), {
    zoom: 8,
    mapTypeControlOptions: {
      mapTypeIds: [
        google.maps.MapTypeId.ROADMAP,
        google.maps.MapTypeId.HYBRID,
        google.maps.MapTypeId.SATELLITE,
        google.maps.MapTypeId.TERRAIN,
        'grayscale'
      ],
      position: google.maps.ControlPosition.TOP_RIGHT,
      style: google.maps.MapTypeControlStyle.DROPDOWN_MENU
    },
    streetViewControl: false
  });

  map.mapTypes.set('grayscale', mapType);
  map.setMapTypeId('grayscale');

  heatmap = new google.maps.visualization.HeatmapLayer({
    data: heatMapPoints,
    radius: 50,
    map: map,
  });

  var heatMapDiv = document.createElement('div');
  var heatMap = new HeatMapControl(heatMapDiv, map);

  heatMapDiv.index = 1;
  heatMapDiv.style['padding-top'] = '10px';
  heatMapDiv.style['pointer-events'] = 'none';
  map.controls[google.maps.ControlPosition.RIGHT_TOP].push(heatMapDiv);

  var dataset_url = $('body').data('dataset')

  d3.csv(dataset_url, function(error, data) {
    var latmed = d3.median(data, function(d) {
      return d[datasetOptions.latitude_attr];
    })
    var longmed = d3.median(data, function(d) {
      return d[datasetOptions.longitude_attr];
    })
    map.setCenter({
      lat: latmed,
      lng: longmed
    });
    data.forEach(function(data, index) {
      addPoint(data, index)
    });
  });
}

function clearMap() {
  markers.forEach(function(marker) {
    marker.setMap(null);
  })
  markers = [];
  infowindows = [];
}

function addPoint(data, index, color) {
  datasetData[index] = data;

  var contentString = '<div><h4>Profile</h4>';

  for (var key in data) {
    if (data[key] === undefined) {
      continue;
    }
    var value = data[key];
    if (Number(data[key])) {
      var number = Number(data[key]);
      value = Number.isInteger(number) ? number.toString() : parseFloat(Number(data[key]).toFixed(5)).toString();
    }
    contentString += '<b>' + key + '</b>: <code>' + value + '</code><br />';
  }
  contentString += '<br/><button type="button" class="btn btn-default" onclick="showPotentialPoints()">Show</button>';
  contentString += '</div>';

  var infowindow = new google.maps.InfoWindow({
    content: contentString
  });

  var marker = new google.maps.Marker({
    position: new google.maps.LatLng(data[datasetOptions.latitude_attr], data[datasetOptions.longitude_attr]),
    map: map,
    icon: {
      path: google.maps.SymbolPath.CIRCLE,
      scale: 7,
      fillColor: (typeof color === 'string' ? color : '#2196F3'),
      fillOpacity: 0.75,
      strokeWeight: 0
    },
    pointId: index,
  })

  marker.addListener('click', function() {
    if (infowindowsOpened != null) {
      infowindowsOpened.close();
    }
    infowindow.open(map, marker);
    infowindowsOpened = infowindow;
    pointChoice = this.pointId;
  })

  infowindows[marker.pointId] = infowindow;
  markers[marker.pointId] = marker;
}

function showPotentialPoints() {
  if (runningRequest === false) {
    runningRequest == true;
    var loader = new XMLHttpRequest();
    loader.onreadystatechange = function() {
      if (this.status == 200 && this.readyState == XMLHttpRequest.DONE) {
        var jsonResponse = JSON.parse(this.responseText)
        clearMap()
        addPoint(datasetData[pointChoice], pointChoice, '#F44336')
        jsonResponse.points.forEach(function(index) {
          addPoint(datasetData[index], index)
        })
      }
      runningRequest == false;
    }
    var url = '/environment/' + datasetOptions.filename + '/' + pointChoice + '/iuga'

    url += '?limit=' + document.getElementById("timelimit").value
    url += '&sigma=' + document.getElementById("sigma").value
    url += '&k=' + document.getElementById("kvalue").value

    loader.open('GET', url, true);
    // loader.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    loader.send();
  }
}
