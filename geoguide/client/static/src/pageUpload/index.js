'use strict'

const identityLatLng = headers => {
  let potentialLatitudes = []
  let potentialLongitudes = []
  let latitudeAttrSelectElement = document.getElementById('latitudeAttrSelect')
  let longitudeAttSelectElement = document.getElementById('longitudeAttrSelect')
  headers.forEach(header => {
    let option
    if (/([Ll]atitude)/.test(header)) {
      potentialLatitudes.push(header)
      option = document.createElement('option')
      option.text = header
      option.value = header
      latitudeAttrSelectElement.add(option)
      return
    }
    if (/([Ll]ongitude)/.test(header)) {
      potentialLongitudes.push(header)
      option = document.createElement('option')
      option.text = header
      option.value = header
      longitudeAttSelectElement.add(option)
      return
    }
  })
  if (potentialLatitudes.length > 0) {
    latitudeAttrSelectElement.value = potentialLatitudes[0]
    if (potentialLatitudes.length > 1) {
      latitudeAttrSelectElement.parentElement.removeAttribute('hidden')
    }
  } else {
    latitudeAttrSelectElement.parentElement.removeAttribute('hidden')
  }
  if (potentialLongitudes.length > 0) {
    longitudeAttSelectElement.value = potentialLongitudes[0]
    if (potentialLongitudes.length > 1) {
      longitudeAttSelectElement.parentElement.removeAttribute('hidden')
    }
  } else {
    longitudeAttSelectElement.parentElement.removeAttribute('hidden')
  }
}

const identifyDatetime = headers => {
  let potentialDatetimes = []
  let datetimeAttrInputElement = document.getElementById('datetimeAttrInputText')
  headers.forEach(header => {
    if (/time$/.test(header)) {
      potentialDatetimes.push(header)
    }
  })
  datetimeAttrInputElement.value = potentialDatetimes.join(', ')
  datetimeAttrInputElement.parentElement.removeAttribute('hidden')
}

const identifyNumberOfRows = contents => {
  let n = (contents.match(/\n/g) || []).length
  let numberRowsInputElement = document.getElementById('numberRowsInputNumber')
  numberRowsInputElement.value = n.toString()
  numberRowsInputElement.parentElement.removeAttribute('hidden')
}

const normalizeHeaders = headers => {
  return headers.map(header => header.replace(/^"|"$/g, ''))
}

const readSingleFile = evt => {
  let f = evt.target.files[0]
  if (f) {
    let r = new window.FileReader()
    r.onload = e => {
      let contents = e.target.result.trim()
      let headers = contents.substr(0, contents.indexOf('\n')).split(',')
      headers = normalizeHeaders(headers)
      identifyDatetime(headers)
      identityLatLng(headers)
      identifyNumberOfRows(contents)
    }
    r.readAsText(f)
  }
}

if (window.File && window.FileReader && window.FileList && window.Blob) {
  document.getElementById('datasetInputFile').addEventListener('change', readSingleFile, false)
} else {
  document.getElementById('latitudeAttrInputText').parentElement.removeAttribute('hidden')
  document.getElementById('longitudeAttrInputText').parentElement.removeAttribute('hidden')
}
