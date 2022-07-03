const _ = require("lodash");
const { rows } = require("./rows");

const columns = {
    getNumberOfInputColumns: (sample) => { return sample.input.length; },
    getNumberOfOutputColumns: (sample) => { return sample.output.length; },
    getInputColumn: (sample, column) => { return sample.input.map(row => row[column-1])},
    getOutputColumn: (sample, column)  => { return sample.output.map(row => row[column-1]) },
    areInputAndOutputColumnsOfTheSameSize: (sample) => {
        return columns.getNumberOfInputColumns(sample) === columns.getNumberOfOutputColumns(sample)
    },
    areThereMoreInputColumnsThanOutputColumns: (sample) => {
        return columns.getNumberOfInputColumns(sample) > columns.getNumberOfOutputColumns(sample)
    },
    isTheOutputOneColumnWide: (sample) => { return sample.output[0].length === 1 },
    doesTheOutputColumnMatchAnyColumnsOfTheInput: (sample) => {
        let match = false;
        let outputColumn = columns.getOutputColumn(sample, 1);
        let numberOfInputColumns = columns.getNumberOfInputColumns(sample); /*?*/
        for(let column= 1; column <= numberOfInputColumns; column++ ) {
            let inputColumn = columns.getInputColumn(sample, column);
            if( _.isEqual( inputColumn, outputColumn)) match = true
        }
        return match; /*?*/
    },
    areAllColumnsEqual: (matrix) => {
        let matrixTranspose = _.unzip(matrix);
        return 0 === matrixTranspose.filter((r, i) => !_.isEqual(r, matrixTranspose[0] ) ).length
    },
    processInputAndOutputHavingColumnsOfTheSameSize: (sample) => {
        if(columns.isTheOutputOneColumnWide(sample)) {
            if(columns.doesTheOutputColumnMatchAnyColumnsOfTheInput(sample)) {
                if(columns.areAllColumnsEqual(sample.input)) {
                    return sample.output; /*?*/
                }
            }
        }
    }
}
exports.columns = columns
