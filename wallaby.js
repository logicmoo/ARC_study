module.exports = function () {
  return {
    files: [
      'data/training/746b3537.json',
      'src/utility/utils.js',
      'src/sanity_check.js',
      'src/solve_task.js'
    ],
    tests: [
//      'tests/utils.test.js'
      'tests/sanity_check.test.js',
      'tests/solve_task.test.js'
    ],

    env: {
      type: 'node',
      runner: 'node'
    },

    testFramework: 'jest'

  };
};
