const { rows } = require('../src/rows')
const { grids } = require('../src/grids')

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



