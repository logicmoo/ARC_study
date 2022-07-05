const _ = require('lodash')
const { sanityCheck } = require("./sanity_check");
const { rows } = require("./rows")
const { columns } = require("./columns")
const { grids } = require("./grids")


function solve_sample(sample) {

    let patternDetected = '';
    if(grids.doInputAndOutputGridsHaveTheSameDimensions(sample)) {
        if(grids.areInputAndOutputGridsIdentical(sample))
            return sample.output
        patternDetected += "grids have same dimension |"
    }

    let solution

    if(columns.areInputAndOutputColumnsOfTheSameSize(sample)) {
        solution = columns.processInputAndOutputHavingColumnsOfTheSameSize(sample)
        if (solution) return sample.output
        patternDetected += "input and output columns have same size |"
    }

    if(rows.areInputAndOutputRowsOfTheSameSize(sample)) {
        solution = rows.processInputAndOutputHavingRowsOfTheSameSize(sample)
        if (solution) return sample.output;
        patternDetected += "input and output rows have the same size |"
    }

    // Now we know rows and columns are different
    if(rows.isTheOutputOneRowHigh(sample)) {
        if(columns.areThereMoreInputColumnsThanOutputColumns(sample)) {
            sample.input = grids.dedupColumns(sample.input);
            solution = rows.processInputAndOutputHavingRowsOfTheSameSize(sample);
            if(solution) return sample.output;
        }
        patternDetected += "output is one row high |"
    }

    if(columns.isTheOutputOneColumnWide(sample)) {
        if(rows.areThereMoreInputRowsThanOutputRows(sample)) {
            sample.input = grids.dedupRows(sample.input);
            solution = columns.processInputAndOutputHavingColumnsOfTheSameSize(sample);
            if(solution) return sample.output;
        }
        patternDetected += "output is one column wide |"
    }

    // console.log('rows.getInputOutputRowScalingFactor(sample) ', rows.getInputOutputRowScalingFactor(sample) );
    // console.log('columns.getInputOutputColumnScalingFactor(sample) ', columns.getInputOutputColumnScalingFactor(sample) );
    // console.log('rows.getOutputInputRowScalingFactor(sample) ', rows.getOutputInputRowScalingFactor(sample) );
    // console.log('columns.getOutputInputColumnScalingFactor(sample) ', columns.getOutputInputColumnScalingFactor(sample) );

    // input is scaled DOWN by the same integer factor in rows and columns
    if( rows.getInputOutputRowScalingFactor(sample) === Math.floor(rows.getInputOutputRowScalingFactor(sample)) &&
        rows.getInputOutputRowScalingFactor(sample) < 1.0 &&
        rows.getInputOutputRowScalingFactor(sample) === columns.getInputOutputColumnScalingFactor(sample) ) {
        patternDetected += 'scales down an integer multiple in rows and columns |'
    }

    // input is scaled UP by the same integer factor in rows and columns
    if( rows.getOutputInputRowScalingFactor(sample) === Math.floor(rows.getOutputInputRowScalingFactor(sample)) &&
        rows.getOutputInputRowScalingFactor(sample) > 1.0 &&
        rows.getOutputInputRowScalingFactor(sample) === columns.getOutputInputColumnScalingFactor(sample) ) {

        // are there copies of the input in the  output?
        //   are they exact copies?  (in number of cells)
        //   how many are there?  what are their colors
        //   OR:  if input is scaled and overlaid on the output, do all black regions overlap all black regions?
        //    OR: if input regions are scaled and overlaid on output, what regions are no longer identical?

        patternDetected += 'scales up an integer multiple in rows and columns |'
    }


    return "no solution:   "  + patternDetected
}

function solve_task(task, training_sample) {
    let err = sanityCheck(task)
    if(err !== 'sane') return err

    if(training_sample)
        return solve_sample(task.train[training_sample-1])

    return solve_sample(task.test[0])
}
exports.solveTask = solve_task;
