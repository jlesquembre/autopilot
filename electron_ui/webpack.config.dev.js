var path = require('path');
var webpack = require('webpack');
const webpackTargetElectronRenderer = require('webpack-target-electron-renderer');



config = {
  debug: true,

  devtool: 'cheap-module-eval-source-map',
  entry: [
    //'eventsource-polyfill', // necessary for hot reloading with IE
    //'webpack-hot-middleware/client',
    'webpack-hot-middleware/client?path=http://localhost:3030/__webpack_hmr',
    //'webpack-dev-server/client?http://localhost:8080',
    'webpack/hot/dev-server', // For hot style updates
    './src/index'
  ],
  //output: {
  //  path: path.join(__dirname, 'dist'),
  //  filename: 'bundle.js',
  //  publicPath: '/static/'
  //},
  output: {
    path: path.join(__dirname, 'dist'),
    publicPath: 'http://localhost:3030/dist/',
    filename: 'bundle.js',
    libraryTarget: 'commonjs2'
  },
  plugins: [
    new webpack.HotModuleReplacementPlugin(),
    new webpack.NoErrorsPlugin()
  ],
  postcss: function (webpack) {
    return [
      //require("postcss-import")({ addDependencyTo: webpack }),
      //require("postcss-url")(),
      require("postcss-cssnext")(),
      // add your "plugins" here
      // ...
      // and if you want to compress,
      // just use css-loader option that already use cssnano under the hood
      require("postcss-browser-reporter")(),
      require("postcss-reporter")()
    ]
  },
  resolve: {
    extensions: ['', '.js', '.jsx'],
    packageMains: ['webpack', 'browser', 'web', 'browserify', ['jam', 'main'], 'main']
  },
  module: {
    loaders: [{
      test: /\.js$/,
      loaders: ['babel'],
      include: path.join(__dirname, 'src')
    },
    {
      test: /\.css$/,
      loader: 'style-loader!css-loader?modules&sourceMap&importLoaders=1&localIdentName=[name]__[local]___[hash:base64:5]!postcss-loader'
    }
    ]
  }
};



config.target = webpackTargetElectronRenderer(config);
module.exports = config;
