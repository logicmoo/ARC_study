const { solveTask } = require('../src/solve_task')


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
        expect(solveTask(task_746B3537, 5)).toStrictEqual([[4], [2], [8], [3] ] )
    });

    // Final solution to task_746B3537
    it('should give the solution to task_746B3537 test as [ [ 1, 2, 3, 8, 4 ] ]', function () {
        expect(solveTask(task_746B3537)).toBe(task_746B3537.test[0].output)
    });

});

