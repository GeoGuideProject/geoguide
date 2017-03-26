const webpack = require('webpack')
const path = require('path')

const config = {
  devtool: 'source-map',
  entry: {
    pageEnvironment: './geoguide/client/static/src/pageEnvironment/index.js',
    pageUpload: './geoguide/client/static/src/pageUpload/index.js'
  },
  output: {
    path: path.resolve(__dirname, 'geoguide/client/static/dist'),
    filename: '[name].js'
  },
  module: {
    rules: [{
      test: /\.(js|jsx)$/,
      exclude: /(node_modules|bower_components)/,
      use: 'babel-loader'
    }, {
      test: /\.css$/,
      use: [{
        loader: 'style-loader'
      }, {
        loader: 'css-loader'
      }]
    }]
  },
  plugins: [
    new webpack.optimize.UglifyJsPlugin(),
    new webpack.optimize.CommonsChunkPlugin({
      name: 'commons'
    })
  ]
}

module.exports = config
