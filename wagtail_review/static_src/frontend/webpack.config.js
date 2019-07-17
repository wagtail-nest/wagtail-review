const path = require('path');

module.exports = {
  entry: './src/main.js',
  externals: {
    annotator: 'annotator',
  },
  output: {
    path: path.resolve(__dirname, '../../static/wagtail_review/js'),
    filename: 'wagtail-review-frontend.js',
    libraryTarget: 'umd',
    library: 'WagtailReview'
  }
};
