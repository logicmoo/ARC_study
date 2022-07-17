const {columns} = require("./columns");
const {rows} = require("./rows");
const _ = require("lodash");

const grids = {
    doInputAndOutputGridsHaveTheSameDimensions: (sample) => {
        return columns.areInputAndOutputColumnsOfTheSameSize(sample) && rows.areInputAndOutputRowsOfTheSameSize(sample)
    },
    areInputAndOutputGridsIdentical: (sample) => {
        // console.log(JSON.stringify(sample.input), JSON.stringify(sample.output))
        return JSON.stringify(sample.input) === JSON.stringify(sample.output)
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
    isInputSquare: (sample) => { return rows.getNumberOfInputRows(sample) === columns.getNumberOfInputColumns(sample)},
    isOutputSquare: (sample) => { return rows.getNumberOfOutputRows(sample) === columns.getNumberOfOutputColumns(sample)},
    areInputAndOutputSquare: (sample) => { return grids.isInputSquare(sample) && grids.isOutputSquare(sample)},
    areNeitherInputNorOutputSquare: (sample) => { return !grids.isInputSquare(sample) && !grids.isOutputSquare(sample)},
    areInputSquareAndOutputNotSquare: (sample) => { return grids.isInputSquare(sample) && !grids.isOutputSquare(sample)},
    areInputNotSquareAndOutputSquare: (sample) => { return !grids.isInputSquare(sample) && grids.isOutputSquare(sample)},

    areAllCellsBlack: (matrix) => { return 0 === matrix.filter(row => !rows.isRowAllBlack(row) ).length },
    areAllCellsColored: (matrix) => { return 0 === matrix.filter(row => !rows.isRowAllColored(row) ).length },
    areAllCellsTheSameColor: (matrix) => {
        return 0 === matrix.filter(row => !rows.isRowAllThisOneColor(row, matrix[0][0]) ).length
    },
    areAllCellsOneColorOrBlack: (matrix) => {
        let colors = []
        matrix.forEach(row => {
            // console.log(row, rows.colorsBesidesBlack(row), colors)
            colors = colors.concat(rows.colorsBesidesBlack(row))
        })
        // console.log('colors', colors, [...new Set(colors)])
        return 1 === [...new Set(colors)].length
    },
    areAllCellsNColorsOrBlack: (matrix, n) => {
        let colors = []
        matrix.forEach(row => {
            colors = colors.concat(rows.colorsBesidesBlack(row))
        })
        return n === [...new Set(colors)].length
    },
    colorsBesidesBlack: (matrix) => {  return [... new Set(matrix.flat(2))].filter(color => color !== 0) },
    areAllInputCellsBlack: (sample) => { return grids.areAllCellsBlack(sample.input) },
    areAllOutputCellsBlack: (sample) => { return grids.areAllCellsBlack(sample.output) },
    areAllInputCellsColored: (sample) => { return grids.areAllCellsColored(sample.input) },
    areAllOutputCellsColored: (sample) => { return grids.areAllCellsColored(sample.output) },
    areAllInputCellsTheSameColor: (sample) => { return grids.areAllCellsTheSameColor(sample.input) },
    areAllOutputCellsTheSameColor: (sample) => { return grids.areAllCellsTheSameColor(sample.output) },

    areAllInputCellsOneColorOrBlack: (sample) => { return grids.areAllCellsOneColorOrBlack(sample.input) },
    areAllOutputCellsOneColorOrBlack: (sample) => { return grids.areAllCellsOneColorOrBlack(sample.output) },
    areAllInputAndOutputCellsOneColorOrBlack: (sample) => {
        return grids.areAllCellsOneColorOrBlack(sample.input)
        &&  grids.areAllCellsOneColorOrBlack(sample.output) &&
            _.isEqual(grids.colorsBesidesBlack(sample.input),  grids.colorsBesidesBlack(sample.output))
    },

    areAllInputCellsTwoColorsOrBlack: (sample) => { return grids.areAllCellsNColorsOrBlack(sample.input, 2) },
    areAllOutputCellsTwoColorsOrBlack: (sample) => { return grids.areAllCellsNColorsOrBlack(sample.output, 2) },
    areAllInputAndOutputCellsTwoColorsOrBlack: (sample) => {
        return grids.areAllCellsNColorsOrBlack(sample.input, 2)
        &&  grids.areAllCellsNColorsOrBlack(sample.output, 2) &&
            _.isEqual(grids.colorsBesidesBlack(sample.input, 2),  grids.colorsBesidesBlack(sample.output, 2))
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
