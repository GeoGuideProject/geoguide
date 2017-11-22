'use strict'

import d3 from 'd3'

let colorModifierElement = document.querySelector('#colorModifier')
let colorModifier = colorModifierElement.value
let colorModifierMax = {}

let sizeModifierElement = document.querySelector('#sizeModifier')
let sizeModifier = sizeModifierElement.value
let sizeModifierMax = {}

export const updateModifiers = (ls) => {
	colorModifier = ls["colorModifier"]
	sizeModifier  = ls["sizeModifier"]
}

const normalfillColor = '#2196F3'
const selectedFillColor = '#F44336'
const iugaFillColor = '#FFC107'
const normalFillColors = [
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
const iugaFillColors = [
  '#fff8e1',
  '#ffecb3',
  '#ffe082',
  '#ffd54f',
  '#ffca28',
  '#ffc107',
  '#ffb300',
  '#ffa000',
  '#ff8f00',
  '#ff6f00'
]

colorModifierElement.addEventListener('change', e => {
  colorModifier = e.target.value
})

sizeModifierElement.addEventListener('change', e => {
  sizeModifier = e.target.value
})

export const onColorModifierChange = f => {
  colorModifierElement.addEventListener('change', f)
}

export const onSizeModifierChange = f => {
  sizeModifierElement.addEventListener('change', f)
}

export const getColor = (data, isSelected, isIugaPoint) => {
  let fillColor = normalfillColor

  if (isSelected) {
    fillColor = selectedFillColor
  } else {
    if (colorModifier !== '' && data[colorModifier]) {
      let n = Number(data[colorModifier])
      n += (2 * Math.abs(n))
      let value = Math.floor((n / colorModifierMax[colorModifier]) * (normalFillColors.length - 1))
      fillColor = isIugaPoint ? iugaFillColors[value] : normalFillColors[value]
    } else if (isIugaPoint) {
      fillColor = iugaFillColor
    }
  }

  return fillColor
}

export const getSize = (data, isSelected, isIugaPoint) => {
  let size = 7
  let sizeBonus = 0

  if (isSelected) {
    size = 7
    sizeBonus = 2
  } else {
    if (sizeModifier !== '' && data[sizeModifier]) {
      let n = Number(data[sizeModifier])
      n += (2 * Math.abs(n))
      size = 5 + ((n / sizeModifierMax[sizeModifier]) * 6)
    }

    if (isIugaPoint) {
      size = 7
      sizeBonus = 2
    }
  }

  return { size, sizeBonus }
}

export const calculateMax = (dataset) => {
  if (colorModifier !== '' && dataset[0][colorModifier]) {
    if (colorModifierMax[colorModifier] === undefined) {
      colorModifierMax[colorModifier] = d3.max(dataset, d => {
        let n = Number(d[colorModifier])
        return n + (2 * Math.abs(n))
      })
    }
  }
  if (sizeModifier !== '' && dataset[0][sizeModifier]) {
    if (sizeModifierMax[sizeModifier] === undefined) {
      sizeModifierMax[sizeModifier] = d3.max(dataset, d => {
        let n = Number(d[sizeModifier])
        return n + (2 * Math.abs(n))
      })
    }
  }
}

export const clearMax = () => {
  colorModifierMax = {}
  sizeModifierMax = {}
}
