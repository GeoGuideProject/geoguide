'use strict'

function identityLatLng(headers) {
  var potentialLatitudes = []
  var potentialLongitudes = []
  var latitudeAttrInputElement = document.getElementById('latitudeAttrInputText')
  var longitudeAttrInputElement = document.getElementById('longitudeAttrInputText')
  headers.forEach(function(header) {
    if (/([Ll]atitude)/.test(header)) {
      potentialLatitudes.push(header)
      return
    }
    if (/([Ll]ongitude)/.test(header)) {
      potentialLongitudes.push(header)
      return
    }
  })
  if (potentialLatitudes.length > 0) {
    latitudeAttrInputElement.value = potentialLatitudes[0]
    if (potentialLatitudes.length > 1) {
      latitudeAttrInputElement.parentElement.removeAttribute('hidden')
    }
  } else {
    latitudeAttrInputElement.parentElement.removeAttribute('hidden')
  }
  if (potentialLongitudes.length > 0) {
    longitudeAttrInputElement.value = potentialLongitudes[0]
    if (potentialLongitudes.length > 1) {
      longitudeAttrInputElement.parentElement.removeAttribute('hidden')
    }
  } else {
    longitudeAttrInputElement.parentElement.removeAttribute('hidden')
  }
}

function identifyDatetime(headers) {
  var potentialDatetimes = []
  var datetimeAttrInputElement = document.getElementById('datetimeAttrInputText')
  headers.forEach(function(header) {
    if (/time$/.test(header)) {
      potentialDatetimes.push(header)
    }
  })
  datetimeAttrInputElement.value = potentialDatetimes.join(', ')
  datetimeAttrInputElement.parentElement.removeAttribute('hidden')
}

function normalizeHeaders(headers) {
  return headers.map(function(header) {
    return header.replace(/^"|"$/g, '')
  })
}

if (window.File && window.FileReader && window.FileList && window.Blob) {
  function readSingleFile(evt) {
    var f = evt.target.files[0];

    if (f) {
      var r = new FileReader();
      r.onload = function(e) {
        var contents = e.target.result;
        var headers = contents.substr(0, contents.indexOf('\n')).split(',')
        headers = normalizeHeaders(headers)
        identifyDatetime(headers)
        identityLatLng(headers)
      }
      r.readAsText(f);
    }
  }

  document.getElementById('datasetInputFile').addEventListener('change', readSingleFile, false);
} else {
  document.getElementById('latitudeAttrInputText').parentElement.removeAttribute('hidden')
  document.getElementById('longitudeAttrInputText').parentElement.removeAttribute('hidden')
}
