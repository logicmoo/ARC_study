module.exports = function () {
  return {
    files: [
      'src/utility/utils.js'
    ],
    tests: [
      'tests/utils.test.js'
    ],

    env: {
      type: 'node',
      runner: 'node'
    },

    testFramework: 'jest'

  };
};
