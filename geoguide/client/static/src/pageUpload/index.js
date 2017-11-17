import identifyLatLng from './attribute/identifyLatLng'
import identifyDatetime from './attribute/identifyDatetime'

import identifyNumberOfRows from './meta/identifyNumberOfRows'
import identifyFileName from './meta/identifyFileName'

const normalizeHeaders = headers => {
  return headers.map(header => header.replace(/^"|"$/g, ''))
}

const identifyAttributes = (headers, values) => {
  identifyDatetime(headers, values)
  identifyLatLng(headers, values)
}

const identifyMeta = (contents) => {
  identifyNumberOfRows(contents)
}

const readSingleFile = e => {
  let f = e.target.files[0]
  if (f) {
    let r = new window.FileReader()
    r.onload = e => {
      let contents = e.target.result.trim()
      let headers = contents.substr(0, contents.indexOf('\n')).split(',')
      headers = normalizeHeaders(headers)
      let values = contents.split('\n').slice(1).map(row => {
        return row.split(',').reduce((obj, currentAttr, i) => {
          obj[headers[i]] = currentAttr;
          return obj
        }, {})
      })
      identifyAttributes(headers, values)
      identifyMeta(contents)
    }
    identifyFileName(f)
    r.readAsText(f)
  }
}

if (window.File && window.FileReader && window.FileList && window.Blob) {
  document.getElementById('datasetInputFile').addEventListener('change', readSingleFile, false)
} else {
  document.getElementById('latitudeAttrInputText').parentElement.removeAttribute('hidden')
  document.getElementById('longitudeAttrInputText').parentElement.removeAttribute('hidden')
}
