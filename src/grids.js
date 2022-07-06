const {columns} = require("./columns");
const {rows} = require("./rows");
const _ = require("lodash");

const grids = {
    doInputAndOutputGridsHaveTheSameDimensions: (sample) => {
        return columns.areInputAndOutputColumnsOfTheSameSize(sample) && rows.areInputAndOutputRowsOfTheSameSize(sample)
    },
    areInputAndOutputGridsIdentical: (sample) => {
        return 0 === sample.input.filter((r, i) => !_.isEqual(r, sample.output[i])).length
    },
    isInputGridScaledDownByIntegerFactor: (sample) => {
        return rows.getInputOutputRowScalingFactor(sample) === Math.floor(rows.getInputOutputRowScalingFactor(sample)) &&
                rows.getInputOutputRowScalingFactor(sample) < 1.0 &&
                rows.getInputOutputRowScalingFactor(sample) === columns.getInputOutputColumnScalingFactor(sample)
    },
    isInputGridScaledUpByIntegerFactor: (sample) => {
        return rows.getOutputInputRowScalingFactor(sample) === Math.floor(rows.getOutputInputRowScalingFactor(sample)) &&
            rows.getOutputInputRowScalingFactor(sample) > 1.0 &&
            rows.getOutputInputRowScalingFactor(sample) === columns.getOutputInputColumnScalingFactor(sample)
    },

    // ACTIONS
    //  also transpose with lodash:  _.unzip(matrix);
    transpose: (matrix) => {
        return _.unzip(matrix);
        // return matrix[0].map((col, i) => matrix.map(row => row[i]));
    },
    dedupRows: (matrix) => {
        if(!columns.areAllColumnsEqual(matrix)) return matrix;
        return Object.values(matrix.reduce((r, v) => (r[v] = v, r), {}))
    },
    dedupColumns: (matrix) => {
        if(!rows.areAllRowsEqual(matrix)) return matrix;
        let dedupedRow1 = [... new Set(matrix[0]) ]
        return matrix.map(r => dedupedRow1)
    },

}
exports.grids = grids
