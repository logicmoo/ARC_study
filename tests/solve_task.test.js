const { solveTask } = require('../src/solve_task')
const { rows } = require('../src/rows')
const { grids } = require('../src/grids')
const task_746B3537 = require("../data/training/746b3537.json");


//  all 746B3537 training sample outputs have either 1 row or one column
describe('given 746B3537', function () {
    let task_746B3537 = require('../data/training/746b3537.json')

    it('should have one test sample object', function () {
        // console.log(task_746B3537.test)
        expect(task_746B3537.test.length).toStrictEqual(1);
    });


    it('should give the solution to task_746B3537 train sample 1 as [ [1], [2], [1] ]', function () {
        expect(solveTask(task_746B3537, 1)).toStrictEqual([ [1], [2], [1] ])
    });

    it('should give the solution to task_746B3537 train sample 2 as [ 3, 4, 6 ]', function () {
        expect(solveTask(task_746B3537, 2)).toStrictEqual([[ 3, 4, 6 ]] )
    });

    it('should give the solution to task_746B3537 train sample 3 as [ 2, 3, 8, 1 ]', function () {
        expect(solveTask(task_746B3537, 3)).toStrictEqual([[ 2, 3, 8, 1 ]] )
    });

    it('should give the solution to task_746B3537 train sample 4 as [ [2], [6], [8] ]', function () {
        expect(solveTask(task_746B3537, 4)).toStrictEqual([[2], [6], [8] ] )
    });

    it('should give the solution to task_746B3537 train sample 5 as [ [4], [2], [8], [3] ]', function () {
        expect(solveTask(task_746B3537, 5)).toStrictEqual(task_746B3537.train[4].output)
    });

    // Final solution to task_746B3537
    it('should give the solution to task_746B3537 test as [ [ 1, 2, 3, 8, 4 ] ]', function () {
        expect(solveTask(task_746B3537)).toBe(task_746B3537.test[0].output)
    });

});


describe('input and output grids are identical', function () {
    let task = {
        "train": [
            {
                "input": [
                    [
                        1,
                        1,
                        1
                    ],
                    [
                        2,
                        2,
                        2
                    ],
                    [
                        3,
                        3,
                        3
                    ]
                ],
                "output": [
                    [
                        1,
                        1,
                        1
                    ],
                    [
                        2,
                        2,
                        2
                    ],
                    [
                        3,
                        3,
                        3
                    ]
                ]
            },
        ],
        "test": [
            {
                "input": [
                    [
                        1,
                        1,
                        2,
                        3,
                        3,
                        3,
                        8,
                        8,
                        4
                    ]
                ],
                "output": [
                    [
                        1,
                        2,
                        3,
                        8,
                        4
                    ]
                ]
            }
        ]
    }
    expect(solveTask(task, 1)).toStrictEqual(task.train[0].output)

});

describe('given a matrix with all rows equal', function () {
    let matrix = [
        [1, 2, 3],
        [1, 2, 3],
        [1, 2, 3]
    ]
    it('should return true when comparing all rows', function () {
        expect(rows.areAllRowsEqual(matrix)).toBe(true);
    });
});

describe('given a matrix with one row different', function () {
    let matrix = [
        [1, 2, 3],
        [2, 3, 4],
        [1, 2, 3]
    ]
    it('should return false when comparing all rows', function () {
        expect(rows.areAllRowsEqual(matrix)).toBe(false);
    });
});

describe('given a matrix with one all rows different', function () {
    let matrix = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    it('should return the transpose ', function () {
        expect(grids.transpose(matrix)).toStrictEqual([ [1,4,7], [2,5,8], [3,6,9] ]);
    });
});



