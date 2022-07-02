const { sanityCheck } = require("../src/sanity_check");

describe('given null task', function () {
    let task = null;
    it('should return missing task', function () {
        expect(sanityCheck(task)).toBe('missing task');
    });
});

describe('given task that is not an object', function () {

    describe('given task that is an array', function () {
        let task = [];
        it('should return task should be an object', function () {
            expect(sanityCheck(task)).toBe('task should be an object');
        });
    });

    describe('given task that is a string', function () {
        let task = 'string';
        it('should return task should be an object', function () {
            expect(sanityCheck(task)).toBe('task should be an object');
        });
    });

    describe('given task that is a number', function () {
        let task = 5;
        it('should return task should be an object', function () {
            expect(sanityCheck(task)).toBe('task should be an object');
        });
    });

});

describe('given task that is an object', function () {

    describe('given task that is an empty object', function () {
        let task = {};
        it('should return task should not be an empty object', function () {
            expect(sanityCheck(task)).toBe('task should not be an empty object');
        });
    });

    describe('given task that contains no training data section', function () {
        let task = { "test": '' };
        it('should return task missing training data', function () {
            expect(sanityCheck(task)).toBe('task missing training data');
        });
    });

    describe('given task with training data that is not an array', function () {

        describe('given task with training data that is an object', function () {
            let task = { train: {} };
            it('should return task training data must be an array', function () {
                expect(sanityCheck(task)).toBe('task training data must be an array');
            });
        });

        describe('given task with training data that is a number', function () {
            let task = { train: 5 };
            it('should return task training data must be an array', function () {
                expect(sanityCheck(task)).toBe('task training data must be an array');
            });
        });

        describe('given task with training data that is a string', function () {
            let task = { train: 'string' };
            it('should return task training data must be an array', function () {
                expect(sanityCheck(task)).toBe('task training data must be an array');
            });
        });


    });

    describe('given task with training data that is an empty array', function () {
        let task = { train: [] }
        it('should return task training data must be an array of one or more objects', function () {
            expect(sanityCheck(task)).toBe('task training data must be an array of one or more objects');
        });
    });

    describe('given task with training data that is not array of objects', function () {
        let task = { train: [ 1, 2, 3 ] }
        it('should return task training data must be an array of one or more objects', function () {
            expect(sanityCheck(task)).toBe('task training data array may only contain objects');
        });
    });

    describe('given task with training data with an object missing inputs', function () {
        let task = { train: [ { output: [] } ] }
        it('should return task training data objects missing at least one input', function () {
            expect(sanityCheck(task)).toBe('task training data objects missing at least one input');
        });
    });

    describe('given task with training data with an object missing outputs', function () {
        let task = { train: [ { input: [ 1 ] } ] }
        it('should return task training data objects missing at least one output', function () {
            expect(sanityCheck(task)).toBe('task training data objects missing at least one output');
        });
    });

    describe('given training data with input that is not an array', function () {
        let task = { train: [  { input: 1, output: [ [ 1 ] ] } ] }
        it('should return training inputs must be arrays', function () {
            expect(sanityCheck(task)).toBe('training inputs must be arrays');

        });
    });

    describe('given training data with input that has no elements', function () {
        let task = { train: [  { input: [], output: [ [ 1 ] ] } ] }
        it('should return training input arrays must have one or more elements', function () {
            expect(sanityCheck(task)).toBe('training input arrays must have one or more elements');
        });
    });

    describe('given training data with output that is not an array', function () {
        let task = { train: [  { input: [1 ], output: 1 } ] }
        it('should return training inputs must be arrays', function () {
            expect(sanityCheck(task)).toBe('training outputs must be arrays');

        });
    });

    describe('given training data with output that has no elements', function () {
        let task = { train: [  { input: [ [ 1 ] ], output: [ ] } ] }
        it('should return training output arrays must have one or more elements', function () {
            expect(sanityCheck(task)).toBe('training output arrays must have one or more elements');
        });
    });

    describe('given training data with input array element that is not an array of arrays', function () {
        let task = { train: [  { input: [ 1, 2 ], output: [ [ 3 ] ] } ] }
        it('should return training input array elements must be arrays', function () {
            expect(sanityCheck(task)).toBe('training input array elements must be arrays');
        });
    });

    describe('given training data with output array element that is not an array of arrays', function () {
        let task = { train: [  { input: [ [1], [2] ], output: [ 3, 4 ] } ] }
        it('should return training output array elements must be arrays', function () {
            expect(sanityCheck(task)).toBe('training output array elements must be arrays');
        });
    });

    describe('given training data with input array element that is not an array of arrays', function () {
        let task = { train: [  { input: [ 1, 2 ], output: [ [ 3 ] ] } ] }
        it('should return training input array elements must be arrays', function () {
            expect(sanityCheck(task)).toBe('training input array elements must be arrays');
        });
    });


});
