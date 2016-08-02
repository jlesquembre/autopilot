var path = require('path');
var webpack = require('webpack');
const webpackTargetElectronRenderer = require('webpack-target-electron-renderer');

//const ExtractTextPlugin = require('extract-text-webpack-plugin');

//var normalize = require('style!raw!normalize.css/normalize.css');



config = {
  //debug: true,

  //devtool: 'eval',
  //devtool: 'eval-source-map',
  entry: [
    //'eventsource-polyfill', // necessary for hot reloading with IE
    //'webpack-hot-middleware/client',
    //'webpack-hot-middleware/client?path=http://localhost:3030/__webpack_hmr',
    //'webpack-dev-server/client?http://localhost:8080',
    //'webpack/hot/dev-server', // For hot style updates
    './src/index'
  ],
  //output: {
  //  path: path.join(__dirname, 'dist'),
  //  filename: 'bundle.js',
  //  publicPath: '/static/'
  //},
  output: {
    path: path.join(__dirname, 'dist'),
    //publicPath: 'http://localhost:3030/dist/',
    //filename: 'bundle.[hash].js',
    filename: 'bundle.js',
    //libraryTarget: 'commonjs2'
  },
  plugins: [
    //new webpack.HotModuleReplacementPlugin(),
    //new webpack.NoErrorsPlugin()
    //new webpack.DefinePlugin({
    //    'process.env.NODE_ENV': '"production"'
    //  }),
    //new webpack.optimize.UglifyJsPlugin({
    //    compress: {
    //      warnings: false
    //    }
    //  })

    new webpack.optimize.OccurenceOrderPlugin(),
    new webpack.DefinePlugin({
      __DEV__: false,
      //'process.env.NODE_ENV': "'production'",
      //'ENV': "'production'",
      'process.env': {
        NODE_ENV: JSON.stringify('production')
      }
    }),
    new webpack.optimize.UglifyJsPlugin({
      //test: /.*\/src\/.*\.js$/,
      //exclude: /.*\/debug-menu\/.*/,
      compressor: {
        screw_ie8: true,
        warnings: false
      }

    }),
    //new ExtractTextPlugin('style.css', { allChunks: true })


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
      //require("cssnano")(),
      //require("postcss-browser-reporter")(),
      //require("postcss-reporter")()
    ]
  },
  resolve: {
    extensions: ['', '.js'],
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
      //loader: 'style-loader!css-loader?minimize&modules&sourceMap&importLoaders=1&localIdentName=[name]__[local]___[hash:base64:5]!postcss-loader'
      loaders: ['style',
                'css?' +
                  'minimize&' +
                  'modules&' +
                  'sourceMap&' +
                  'importLoaders=1&' +
                  'localIdentName=[name]__[local]___[hash:base64:5]',
                //{ loader: 'css',
                //    query: { minimize: 1,
                //             modules: 1,
                //             sourceMap: 1,
                //             importLoaders: 1,
                //             localIdentName: '[name]__[local]___[hash:base64:5]',
                //    }
                //},
                //{ 'css': { minimize: 1,
                //           modules: 1,
                //           sourceMap: 1,
                //           importLoaders: 1,
                //           localIdentName: '[name]__[local]___[hash:base64:5]',
                //    }
                //},
                'postcss'
               ],
    },
    //{
    //  test: /\.sss$/,
    //  loader: 'style-loader!css-loader?modules&sourceMap&importLoaders=1&localIdentName=[name]__[local]___[hash:base64:5]!postcss-loader?parser=sugarss'
    //}
    ]
  }
};



config.target = webpackTargetElectronRenderer(config);
module.exports = config;
