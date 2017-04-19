const identifyLatLng = (headers, values) => {
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

export default identifyLatLng
