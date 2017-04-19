const identifyDatetime = (headers, values) => {
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

export default identifyDatetime
