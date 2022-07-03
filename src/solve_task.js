const _ = require('lodash')
const { sanityCheck } = require("./sanity_check");
const { rows } = require("./rows")
const { columns } = require("./columns")
const { grids } = require("./grids")


function solve_sample(sample) {

    if(grids.doInputAndOutputGridsHaveTheSameDimensions(sample)) {
        if(grids.areInputAndOutputGridsIdentical(sample))
            return sample.output
    }

    let solution

    if(columns.areInputAndOutputColumnsOfTheSameSize(sample)) {
        solution = columns.processInputAndOutputHavingColumnsOfTheSameSize(sample)
        if (solution) return sample.output
    }

    if(rows.areInputAndOutputRowsOfTheSameSize(sample)) {
        solution = rows.processInputAndOutputHavingRowsOfTheSameSize(sample)
        if (solution) return sample.output;
    }

    // Now we know rows and columns are different
    if(rows.isTheOutputOneRowHigh(sample)) {
        if(columns.areThereMoreInputColumnsThanOutputColumns(sample)) {
            sample.input = grids.dedupColumns(sample.input);
            solution = rows.processInputAndOutputHavingRowsOfTheSameSize(sample);  /*?*/
            if(solution) return sample.output;
        }
    }

    if(columns.isTheOutputOneColumnWide(sample)) {
        if(rows.areThereMoreInputRowsThanOutputRows(sample)) {
            sample.input = grids.dedupRows(sample.input);
            solution = columns.processInputAndOutputHavingColumnsOfTheSameSize(sample);  /*?*/
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
