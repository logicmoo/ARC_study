module.exports = function () {
  return {
    files: [
      'src/utility/utils.js',
      'src/sanity_check.js',
      'src/solve_task.js'
    ],
    tests: [
//      'tests/utils.test.js'
      'tests/sanity_check.test.js'
    ],

    env: {
      type: 'node',
      runner: 'node'
    },

    testFramework: 'jest'

  };
};
