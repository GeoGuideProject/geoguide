'use strict'

var pointChoice = -1
var iugaLastId = -1
var map = null
var markerClusterer = null
var markers = {}
var infowindows = {}
var infowindowsOpened = null
var runningRequest = false
var heatmap = null
var heatMap = null
var heatMapPoints = []
var isHeatMap = false
var datasetData = {}
var datasetOptions = JSON.parse(document.querySelector('#dataset_json').innerHTML)
var datasetFilters = datasetOptions.headers;
var colorModifierElement = document.querySelector('#colorModifier')
var colorModifier = colorModifierElement.value
var colorModifierMax = {}
var chartsPerPage = 2
var currentChartIndex = 0

var sizeModifierElement = document.querySelector('#sizeModifier')
var sizeModifier = sizeModifierElement.value
var sizeModifierMax = {}

colorModifierElement.addEventListener('change', function(e) {
  colorModifier = e.target.value
})

sizeModifierElement.addEventListener('change', function(e) {
  sizeModifier = e.target.value
})

function HeatMapControl(controlDiv, map) {
  var control = this;

  controlDiv.style.clear = 'both';

  var heatMapUI = document.createElement('div');
  heatMapUI.id = 'heatMapUI';
  controlDiv.appendChild(heatMapUI);

  var heatMapText = document.createElement('div');
  heatMapText.id = 'heatMapText';
  heatMapText.innerHTML = 'Heatmap';
  heatMapUI.appendChild(heatMapText);

  heatMapUI.addEventListener('click', function() {
    heatMapPoints = Object.values(markers).map(function(marker) {
      marker.setVisible(isHeatMap);
      return marker.position;
    });

    isHeatMap = !isHeatMap;

    if (isHeatMap) {
      heatmap.setData(heatMapPoints);
      heatmap.setMap(map);
      markerClusterer.clearMarkers();
      heatMapText.innerHTML = 'Normal';
    } else {
      heatmap.setMap(null);
      markerClusterer.addMarkers(Object.values(markers));
      heatMapText.innerHTML = 'Heatmap';
    }
    if (infowindowsOpened != null) {
      infowindowsOpened.close();
    }
  });
}

function initMap() {
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
    zoom: 12,
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
    disableDefaultUI: true,
    zoomControl: true,
    mapTypeControl: true,
    zoomControlOptions: {
      position: google.maps.ControlPosition.RIGHT_BOTTOM,
    }
  });

  map.mapTypes.set('grayscale', mapType);
  map.setMapTypeId('grayscale');

  markerClusterer = new MarkerClusterer(map, [], {
      imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m',
      maxZoom: 13,
  });

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

  map.controls[google.maps.ControlPosition.TOP_RIGHT].push(heatMapDiv)

  var customControlsLeftTopElement = document.getElementById('customControlsLeftTop')
  map.controls[google.maps.ControlPosition.LEFT_TOP].push(customControlsLeftTopElement)

  var dataset_url = document.querySelector('body').dataset['dataset']

  d3.csv(dataset_url, function(err, data) {
    processData(err, data)
    processFilter()
  })

  var charts = document.querySelectorAll('.chart')
  Array.prototype.slice.call(charts, 0, chartsPerPage).forEach(function (chart) {
    chart.hidden = false
  })

  var selectElement = document.querySelector('#filtersPerPage')
  if (selectElement) {
      selectElement.selectedIndex = chartsPerPage - 1
  }

  isDatasetReady()
}

function processData(err, data) {
  var latmed = d3.median(data, function(d) {
    return d[datasetOptions.latitude_attr];
  })
  var longmed = d3.median(data, function(d) {
    return d[datasetOptions.longitude_attr];
  })
  calculateMaxModifiers(data)
  map.setCenter({
    lat: latmed,
    lng: longmed
  });

  data.forEach(function(data, index) {
    addPoint(data, index)
  });

  markerClusterer.addMarkers(Object.values(markers))
}

function processFilter(dataset, filters) {
  dataset = dataset || datasetData
  filters = filters || datasetFilters

  d3.selectAll('.chart > svg').remove()

  initFilters(Object.values(dataset));
  createChartFilter(filters, onDataFiltered)

  function onDataFiltered(newData) {
    markerClusterer.clearMarkers()

    Object.keys(markers).forEach(function(x) {
      markers[x].hasMarker = false
    })

    newData.forEach(function(data, index) {
      if (markers[data.geoguide_id] === undefined) {
        addPoint(data, data.geoguide_id, data.geoguide_id === iugaLastId ? '#F44336' : undefined)
      } else {
        markers[data.geoguide_id].hasMarker = true
      }
    })

    Object.keys(markers).forEach(function(x) {
      if (markers[x].hasMarker === false && markers[x].id !== iugaLastId) {
        delete markers[x]
      }
    })

    markerClusterer.addMarkers(Object.values(markers))

    if (isHeatMap) {
      isHeatMap = !isHeatMap;
      document.getElementById('heatMapUI').click();
    }
  };
}

function changeCurrentChart (button) {
  var charts = document.querySelectorAll('.chart')
  var first, last

  if (chartsPerPage === charts.length) {
    return
  }

  charts.forEach(function (e) {
    e.hidden = true
  })

  first = charts[0]
  last = charts[charts.length - 1]

  switch (button.value) {
    case 'Previous':
      first.parentElement.insertBefore(last, first)
      break
    case 'Next':
      last.parentElement.appendChild(first)
      break
    default:
      break
  }
  charts = document.querySelectorAll('.chart')
  for (var i = 0; i < chartsPerPage; i++) {
    charts[i].hidden = false
  }
}

function updateFiltersPage() {
  var e = document.querySelector('#filtersPerPage')
  var value = e.options[e.selectedIndex].value
  var charts = document.querySelectorAll('.chart')

  if (value == '*') {
    chartsPerPage = charts.length
    charts.forEach(function(e) {
      e.hidden = false
    })
  }
  else {
    charts.forEach(function(e) {
      e.hidden = true
    })
    chartsPerPage = Number(value);
    for (var i = 0; i < chartsPerPage; i++) {
      charts[i].hidden = false
    }
  }

  var buttonsContainer = document.querySelector('#collapseFilters .buttons')
  buttonsContainer.hidden = chartsPerPage === charts.length
}

function resetFilters() {
  var charts = document.querySelectorAll('.chart')
  charts.forEach(function (_, i) {
    reset(i)
  })
}

function refreshMap() {
  clearMap()
  resetFilters()
  processData(undefined, Object.values(datasetData))
  processFilter()
  iugaLastId = -1
}

function clearMap() {
  markerClusterer.clearMarkers()
  markers = {}
  infowindows = {}
}

function calculateMaxModifiers(dataset) {
  if (colorModifier !== '' && dataset[0][colorModifier]) {
    if (colorModifierMax[colorModifier] === undefined) {
      colorModifierMax[colorModifier] = d3.max(dataset, function(d) {
        var n = Number(d[colorModifier])
        return n + (2 * Math.abs(n))
      })
    }
  }
  if (sizeModifier !== '' && dataset[0][sizeModifier]) {
    if (sizeModifierMax[sizeModifier] === undefined) {
      sizeModifierMax[sizeModifier] = d3.max(dataset, function(d) {
        var n = Number(d[sizeModifier])
        return n + (2 * Math.abs(n))
      })
    }
  }
}

function refreshModifiers() {
  calculateMaxModifiers(Object.values(datasetData))
  Object.keys(markers).forEach(function(x) {
    var data = datasetData[markers[x].id]
    markers[x].setIcon(getIcon(data, data.geoguide_id === iugaLastId ? '#F44336' : undefined))
  })
}

function getIcon(data, color) {
  var fillColor = '#2196F3'
  var fillColors = [
    '#e3f2fd',
    '#bbdefb',
    '#90caf9',
    '#64b5f6',
    '#42a5f5',
    '#2196f3',
    '#1e88e5',
    '#1976d2',
    '#1565c0',
    '#0d47a1'
  ]

  if (colorModifier !== '' && data[colorModifier]) {
    var n = Number(data[colorModifier])
    n += (2 * Math.abs(n))
    var value = Math.floor((n / colorModifierMax[colorModifier]) * (fillColors.length - 1))
    fillColor = fillColors[value]
  }

  if (typeof color === 'string') {
    fillColor = color
  }

  var size = 7

  if (sizeModifier !== '' && data[sizeModifier]) {
    var n = Number(data[sizeModifier])
    n += (2 * Math.abs(n))
    size = 5 + ((n / sizeModifierMax[sizeModifier]) * 6)
  }

  return {
    path: google.maps.SymbolPath.CIRCLE,
    scale: size,
    fillColor: fillColor,
    fillOpacity: 0.75,
    strokeWeight: 0
  }
}

function addPoint(data, index, color) {
  datasetData[data.geoguide_id] = data;

  var contentString = '<div id="infowindow' + data.geoguide_id + '"><h4>Profile</h4>';

  Object.keys(data).forEach(function(key) {
    if (data[key] === undefined || key === 'geoguide_id') {
      return
    }
    var value = data[key];
    if (Number(data[key])) {
      var number = Number(data[key]);
      value = Number.isInteger(number) ? number.toString() : parseFloat(Number(data[key]).toFixed(5)).toString();
    }
    contentString += '<b>' + key + '</b>: <code>' + value + '</code><br />';
  })
  contentString += '<br/><button type="button" class="btn btn-default" onclick="showPotentialPoints()">Explore</button>';
  contentString += '</div>';

  var infowindow = new google.maps.InfoWindow({
    content: contentString
  });

  var marker = new google.maps.Marker({
    position: new google.maps.LatLng(data[datasetOptions.latitude_attr], data[datasetOptions.longitude_attr]),
    // map: map,
    icon: getIcon(data, color),
    id: data.geoguide_id,
    hasMarker: true,
  })

  marker.addListener('click', function() {
    if (infowindowsOpened != null) {
      infowindowsOpened.close();
    }
    infowindow.open(map, marker);
    infowindowsOpened = infowindow
    pointChoice = this.id
    if (datasetOptions.indexed === false) {
      var btnElement = document.querySelector('#infowindow' + this.id + ' button')

      btnElement.setAttribute('disabled', 'disabled')
      btnElement.setAttribute('title', 'This dataset isn\'t ready yet.')
    }
  })

  // if (markers[marker.id] !== undefined) {
  //   marker.setMap(null)
  // }

  // markerClusterer.addMarker(marker)

  infowindows[marker.id] = infowindow
  markers[marker.id] = marker

  return markers[marker.id]
}

function showPotentialPoints() {
  if (runningRequest === false) {
    runningRequest = true;
    var loader = new XMLHttpRequest();
    var params = null;
    loader.onreadystatechange = function() {
      if (this.readyState === XMLHttpRequest.DONE) {
        if (this.status === 200) {
          var jsonResponse = JSON.parse(this.responseText)
          var points = {}
          clearMap()
          addPoint(datasetData[pointChoice], pointChoice, '#F44336')
          jsonResponse.points.forEach(function (id) {
            if (id === pointChoice) {
              return
            }
            addPoint(datasetData[id], id)
            points[id] = datasetData[id]
          })
          processFilter(points)
          markerClusterer.addMarkers(Object.values(markers))
        } else if (this.status === 202) {
          window.alert('Not ready yet.')
        }
        runningRequest = false
      }
    }
    var url = '/environment/' + datasetOptions.filename + '/' + pointChoice + '/iuga'

    url += '?limit=' + document.getElementById("timelimit").value
    url += '&sigma=' + document.getElementById("sigma").value
    url += '&k=' + document.getElementById("kvalue").value

    if (document.querySelector('#onlyfilteredpoints').checked) {
      if (Object.keys(datasetData).length != Object.keys(markers).length) {
        var filtered_points = Object.keys(markers).map(function(x) {
          return markers[x].id
        });
        params = 'filtered_points=' + filtered_points.join(',')

        if (document.getElementById("kvalue").value > filtered_points.length - 2) {
          alert("You don't have enough filtered points")
          runningRequest = false
          return
        }
      }
    }
    loader.open('POST', url, true)
    loader.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    loader.send(params)
    iugaLastId = pointChoice
  }
}

function isDatasetReady () {
  if (datasetOptions.indexed === false) {
    var req = new window.XMLHttpRequest()
    req.onreadystatechange = function () {
      if (this.status === 200 && this.readyState === window.XMLHttpRequest.DONE) {
        datasetOptions = JSON.parse(this.responseText)
        if (datasetOptions.indexed === false) {
          setTimeout(isDatasetReady, 1000)
        } else if (pointChoice >= 0) {
          var btnElement = document.querySelector('#infowindow' + pointChoice + ' button')
          if (btnElement !== null) {
            btnElement.removeAttribute('disabled')
            btnElement.removeAttribute('title')
          }
        }
      }
    }
    var url = '/environment/' + datasetOptions.filename + '/details'
    req.open('GET', url, true)
    req.send()
  }
}
