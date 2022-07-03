const {columns} = require("./columns");
const {rows} = require("./rows");
const _ = require("lodash");

const grids = {
    doInputAndOutputGridsHaveTheSameDimensions: (sample) => {
        return columns.areInputAndOutputColumnsOfTheSameSize(sample)  && rows.areInputAndOutputRowsOfTheSameSize(sample)
    },
    areInputAndOutputGridsIdentical: (sample) => {
        return 0 === sample.input.filter((r, i) => !_.isEqual(r, sample.output[i] ) ).length
    },
    //  also transpose with lodash:  _.unzip(matrix);
    transpose: (matrix) => {
        return _.unzip(matrix);
        // return matrix[0].map((col, i) => matrix.map(row => row[i]));
    },
    dedupRows: (matrix) => {
        if(!columns.areAllColumnsEqual(matrix)) return matrix;
        return Object.values(matrix.reduce((r, v) => (r[v] = v, r), {}))  /*?*/
    },
    dedupColumns: (matrix) => {
        if(!rows.areAllRowsEqual(matrix)) return matrix;
        let dedupedRow1 = [... new Set(matrix[0]) ]  /*?*/
        return matrix.map(r => dedupedRow1) /*?*/
    },

}
exports.grids = grids
