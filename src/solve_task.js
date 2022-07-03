const utils = require("./utility/utils");
const _ = require('lodash')
const { sanityCheck } = require("./sanity_check");


function getNumberOfInputColumns(sample) { return sample.input.length; }
function getNumberOfInputRows(sample) { return sample.input[0].length; }
function getNumberOfOutputColumns(sample) { return sample.output.length; }
function getNumberOfOutputRows(sample) { return sample.output[0].length; }

function doInputAndOutputHaveTheSameShape(sample) {
    return getNumberOfInputColumns(sample) === getNumberOfOutputColumns(sample)
        && getNumberOfInputRows(sample) === getNumberOfOutputRows(sample)
}

function areColumnsOfTheSameSize(sample) {
    return getNumberOfInputColumns(sample) === getNumberOfOutputColumns(sample)
}

function areRowsOfTheSameSize(sample) {
    return getNumberOfInputRows(sample) === getNumberOfOutputRows(sample)
}

function isTheOutputOneColumnWide(sample) { return sample.output[0].length === 1 }
function isTheOutputOneRowHigh(sample) { return sample.output.length === 1 }

function getInputColumn(sample, column) { return sample.input.map(row => row[column-1])}
function getOutputColumn(sample, column) { return sample.output.map(row => row[column-1]) }

function getInputRow(sample, row) { return sample.input[row-1]; }
function getOutputRow(sample, row) { return sample.output[row-1] }

function doesTheOutputMatchAnyColumnsOfTheInput(sample) {
    let match = false;
    let outputColumn = getOutputColumn(sample, 1);
    for(let column= 1; column < 4; column++ ) {
        let inputColumn = getInputColumn(sample, column);
        if( _.isEqual( inputColumn, outputColumn)) match = true
    }
    return match; /*?*/
}

function doesTheOutputMatchAnyRowsOfTheInput(sample) {
    let match = false;
    let outputRow = getOutputRow(sample, 1);
    for(let row= 1; row < 4; row++ ) {
        let inputRow = getInputRow(sample, row);
        if( _.isEqual( inputRow, outputRow))  match = true
    }
    return match; /*?*/
}

function dedupColumns(matrix) {
    // only do this if all rows are equal
    let row1 = matrix[0]
    if(row1.filter(r => _.isEqual(r, row1)).length > 0)
        return matrix;
    let dedupedRow1 = [... new Set(row1) ]  /*?*/
    return matrix.map(r => dedupedRow1) /*?*/
}

function dedupRows(matrix) {
    return Object.values(matrix.reduce((r, v) => (r[v] = v, r), {}))  /*?*/
}

function processColumnsOfTheSameSize(sample) {
    if(areColumnsOfTheSameSize(sample)) {
        if(isTheOutputOneColumnWide(sample)) {
            if(doesTheOutputMatchAnyColumnsOfTheInput(sample)) {
                return sample.output; /*?*/
            }
        }
    }
}

function processRowsOfTheSameSize(sample) {
    if(areRowsOfTheSameSize(sample)) {
        if(isTheOutputOneRowHigh(sample)) {
            if(doesTheOutputMatchAnyRowsOfTheInput(sample)) {
                return sample.output; /*?*/
            }
        }
    }
}

function solve_sample(sample) {

    if(doInputAndOutputHaveTheSameShape(sample)) {
      // TODO:  this won't work;  rows or columns must be compared one at a time
      if(sample.input === sample.output) return sample.output;
    }

    let solution = processColumnsOfTheSameSize(sample)
    if(solution) return sample.output;

    solution = processRowsOfTheSameSize(sample);
    if(solution) return sample.output;

    // Now we know rows and columns are different
    if(isTheOutputOneRowHigh(sample)) {
        if(getNumberOfInputColumns(sample) > getNumberOfOutputColumns(sample)) {
            sample.input = dedupColumns(sample.input);
            solution = processRowsOfTheSameSize(sample);  /*?*/
            if(solution) return sample.output;
        }
    }

    if(isTheOutputOneColumnWide(sample)) {
        if(getNumberOfInputRows(sample) > getNumberOfOutputRows(sample)) {
            sample.input = dedupRows(sample.input);
            solution = processColumnsOfTheSameSize(sample);  /*?*/
            if(solution) return sample.output;
        }

    }
    // if we de-dup columns
}

function solve_task(task, training_sample) {
    let err = sanityCheck(task)
    if(err !== 'sane') return err

    if(training_sample)
        return solve_sample(task.train[training_sample-1])

    return solve_sample(task.test[0])
}
exports.solveTask = solve_task;
