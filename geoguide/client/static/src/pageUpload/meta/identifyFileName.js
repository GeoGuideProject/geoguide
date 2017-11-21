const identifyFileName = file => {
  let filename = file.name.split('.')[0].split('-').join(' ')
	let titleInputElement = document.getElementById('titleInputText')
  titleInputElement.value = filename
}

export default identifyFileName
