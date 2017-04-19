const identifyNumberOfRows = contents => {
  let n = (contents.match(/\n/g) || []).length
  let numberRowsInputElement = document.getElementById('numberRowsInputNumber')
  numberRowsInputElement.value = n.toString()
  numberRowsInputElement.parentElement.removeAttribute('hidden')
}

export default identifyNumberOfRows
