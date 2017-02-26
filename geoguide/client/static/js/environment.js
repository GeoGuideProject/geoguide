'use strict'

var pointChoice = -1
var iugaLastPointId = -1
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
var dataFiltered = null
var datasetOptions = JSON.parse(document.querySelector('#dataset_json').innerHTML)
var datasetHeaders = datasetOptions.headers;
var colorModifierElement = document.querySelector('#colorModifier')
var colorModifier = colorModifierElement.value
var colorModifierMax = {}
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

  d3.csv(dataset_url, function(err, data){
    processData(err, data);
    processFilter();
  });

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
    data.pointId = index;
    addPoint(data, index)
  });
}

function processFilter(){

  initFilters(datasetData);

  createChartFilter(datasetHeaders, onDataFiltered);

  var charts = document.getElementsByClassName('chart')[0].hidden = false;

  function onDataFiltered(newData) {
    for (var i = 0; i < markers.length; i++) {
      markers[i].hasMarker = false;
    }

    newData.forEach(function(data, index) {
      if (markers.length > 0) {
        var pointAlreadyExist = false;
        for (var i = 0; i < markers.length; i++) {
          if (markers[i].pointId == data.pointId)
          {
            markers[i].hasMarker = true;
            pointAlreadyExist = true;
            break;
          }
        }
        if (pointAlreadyExist)
          return;
      }
      addPoint(data, index)
    });

    var oldPoints = markers.length - newData.length;
    var i = 0;
    while(oldPoints > 0)
    {
      if (!markers[i].hasMarker)
      {
        markers[i].setMap(null);
        markers.splice(i, 1);
        oldPoints--;
      }
      else {
        i++;
      }
    }

    if (isHeatMap) {
      isHeatMap = !isHeatMap;
      document.getElementById('heatMapUI').click();
    }
  };
}

function changeCurrentChart(button) {

  var charts = document.getElementsByClassName('chart');

  charts[currentChartIndex].hidden = true;

  switch (button.value) {
    case 'Previous':
      currentChartIndex = currentChartIndex == 0 ? charts.length - 1 : currentChartIndex - 1;
      break;
    case 'Next':
      currentChartIndex = currentChartIndex == charts.length - 1 ? 0 : currentChartIndex + 1;
      break;
  }

  charts[currentChartIndex].hidden = false;
}

function refreshMap() {
  clearMap()
  processData(undefined, datasetData)
  iugaLastPointId = -1
}

function clearMap() {
  markers.forEach(function(marker) {
    marker.setMap(null);
  })
  markers = [];
  infowindows = [];
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
  calculateMaxModifiers(datasetData)
  markers.forEach(function(marker) {
    var data = datasetData[marker.pointId]
    marker.setIcon(getIcon(data,  marker.pointId === iugaLastPointId ? '#F44336' : undefined))
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
    '#0d47a1',
    '#82b1ff',
    '#448aff',
    '#2979ff',
    '#2962ff',
  ]

  if (colorModifier !== '' && data[colorModifier]) {
    var value = Math.floor((Math.abs(Number(data[colorModifier])) / colorModifierMax[colorModifier]) * (fillColors.length - 1))
    fillColor = fillColors[value]
  }

  if (typeof color === 'string') {
    fillColor = color;
  }

  var size = 7
  var sizes = [5, 7, 9, 11]

  if (sizeModifier !== '' && data[sizeModifier]) {
    var value = Math.floor((Math.abs(Number(data[sizeModifier])) / sizeModifierMax[sizeModifier]) * (sizes.length - 1))
    size = sizes[value]
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
  datasetData[index] = data;

  var contentString = '<div id="infowindow' + index + '"><h4>Profile</h4>';

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
    icon: getIcon(data, color),
    pointId: datasetData[index].pointId,
    hasMarker: true,
  })

  marker.addListener('click', function() {
    if (infowindowsOpened != null) {
      infowindowsOpened.close();
    }
    infowindow.open(map, marker);
    infowindowsOpened = infowindow;
    pointChoice = this.pointId;
    if (datasetOptions.indexed === false) {
      var btnElement = document.querySelector('#infowindow' + this.pointId + ' button')

      btnElement.setAttribute('disabled', 'disabled')
      btnElement.setAttribute('title', 'This dataset isn\'t ready yet.')
    }
  })

  if (markers[marker.pointId]) {
    marker.setMap(null);
  }

  infowindows[marker.pointId] = infowindow;
  markers.push(marker);
}

function showPotentialPoints() {
  if (runningRequest === false) {
    runningRequest = true;
    var loader = new XMLHttpRequest();
    loader.onreadystatechange = function() {
      if (this.readyState === XMLHttpRequest.DONE) {
        if (this.status === 200) {
          var jsonResponse = JSON.parse(this.responseText)
          clearMap()
          addPoint(datasetData[pointChoice], pointChoice, '#F44336')
          jsonResponse.points.forEach(function(index) {
            if (index === pointChoice) {
              return
            }
            addPoint(datasetData[index], index)
          })
        }
        else if (this.status === 202) {
          alert('Not ready yet.')
        }
        runningRequest = false;
      }
    }
    var url = '/environment/' + datasetOptions.filename + '/' + pointChoice + '/iuga'

    url += '?limit=' + document.getElementById("timelimit").value
    url += '&sigma=' + document.getElementById("sigma").value
    url += '&k=' + document.getElementById("kvalue").value

    loader.open('GET', url, true);
    // loader.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    loader.send();
    iugaLastPointId = pointChoice
  }
}

function isDatasetReady() {
  console.log(datasetOptions.indexed)
  if (datasetOptions.indexed === false) {
    var req = new XMLHttpRequest();
    req.onreadystatechange = function() {
      if (this.status === 200 && this.readyState === XMLHttpRequest.DONE) {
        datasetOptions = JSON.parse(this.responseText)
        if (datasetOptions.indexed === false) {
          setTimeout(isDatasetReady, 1000);
        } else if (pointChoice >= 0) {
          var btnElement = document.querySelector('#infowindow' + pointChoice + ' button')

          btnElement.removeAttribute('disabled')
          btnElement.removeAttribute('title')
        }
      }
    }
    var url = '/environment/' + datasetOptions.filename + '/details'
    req.open('GET', url, true)
    req.send()
  }
}
