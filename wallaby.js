module.exports = function () {
  return {
    files: [
      'data/training/*.json',
      'src/utility/utils.js',
      'src/sanity_check.js',
      'src/rows.js',
      'src/columns.js',
      'src/grids.js',
      'src/solve_task.js',
      'tests/tasks.js',
    ],
    tests: [
        'tests/*.test.js',
        'tests/auto/*.test.js',
    ],

    env: {
      type: 'node',
      runner: 'node'
    },

    testFramework: 'jest'

  };
};
