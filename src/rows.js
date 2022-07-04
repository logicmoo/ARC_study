const _ = require("lodash");

const rows = {
    getNumberOfInputRows: (sample) => { return sample.input[0].length; },
    getNumberOfOutputRows: (sample) => { return sample.output[0].length; },
    getInputRow: (sample, row) => { return sample.input[row-1]; },
    getOutputRow: (sample, row) => { return sample.output[row-1] },
    areInputAndOutputRowsOfTheSameSize: (sample) => {
        return rows.getNumberOfInputRows(sample) === rows.getNumberOfOutputRows(sample)
    },
    areThereMoreInputRowsThanOutputRows: (sample) => {
        return  rows.getNumberOfInputRows(sample) > rows.getNumberOfOutputRows(sample)
    },
    isTheOutputOneRowHigh: (sample) => { return sample.output.length === 1 },
    doesTheOutputRowMatchAnyRowsOfTheInput: (sample) => {
        return 0 === sample.input.filter((r, i) => !_.isEqual(r, rows.getOutputRow(sample, 1) ) ).length
    },
    areAllRowsEqual: (matrix) => {
        return 0 === matrix.filter((r, i) => !_.isEqual(r, matrix[0] ) ).length
    },
    processInputAndOutputHavingRowsOfTheSameSize: (sample) => {
        if(rows.isTheOutputOneRowHigh(sample)) {
            if(rows.doesTheOutputRowMatchAnyRowsOfTheInput(sample)) {
                if(rows.areAllRowsEqual(sample.input)) {
                    return sample.output;
                }
            }
        }
    }
}
exports.rows = rows
