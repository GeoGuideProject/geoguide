'use strict'

import GreatCircle from 'great-circle'

export const st_dbscan = (df, spatial_threshold = 1000, temporal_threshold = 10, min_neighbors = 5) => {
	let cluster_label = 0

	const unmarked = 777777
	let stack = []

	df = df.map(point => { point[3] = unmarked; return point })

	for (let index = 0; index < df.length; index++){
		if (df[index][3] == unmarked) {
			let neighborhood = retrieve_neighbors(index, df, spatial_threshold, temporal_threshold)

			if (neighborhood.length < min_neighbors) {
				df[index][3] = -1
			} else {
				df[index][3] = ++cluster_label

				neighborhood.forEach((neig_number, index) => {
					df[neig_number][3] = cluster_label
					stack.push(neig_number)
				})

				while (stack.length > 0) {
					const current_point_index = stack.pop()
					const new_neighborhood = retrieve_neighbors(current_point_index, df, spatial_threshold, temporal_threshold)

					if (new_neighborhood.length >= min_neighbors) {
						new_neighborhood.forEach((neig_number) => {
							let npoint = df[neig_number]
							if (npoint[3] != -1 && npoint[3] == unmarked) {
								// TODO: verify cluster average
								df[neig_number][3] = cluster_label
								stack.push(neig_number)
							}
						})
					}
				}
			}
		}
	}	
	return df.map((e, i) => e[3]).filter((e, i, self) => self.indexOf(e) === i)
		.map((e, i) => {return {"cluster": e, "points": df.filter((ele, ind) => ele[3] == e)}})
}

const retrieve_neighbors = (index_center, df, spatial_threshold, temporal_threshold) => {
	let neighborhood = []
	const center_point = df[index_center]
	const center_point_date = new Date(center_point[2])

	const min_time = center_point_date.getTime() - temporal_threshold*1000
	const max_time = center_point_date.getTime() + temporal_threshold*1000

	for (let i = 0; i < df.length; i++) {
		const point = df[i];
		const point_date = new Date(point[2])
		if (point_date >= min_time && point_date <= max_time && i != index_center) {
			const distance = GreatCircle.distance(center_point[0], center_point[1], point[0], point[1], "M")
			if (distance <= spatial_threshold)
				neighborhood.push(i)
		}
	}

	return neighborhood
}
