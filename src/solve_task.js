const _ = require('lodash')
const { sanityCheck } = require("./sanity_check");
const { rows } = require("./rows")
const { columns } = require("./columns")
const { grids } = require("./grids")


function solve_sample(sample) {

    let failReason = '';
    if(grids.doInputAndOutputGridsHaveTheSameDimensions(sample)) {
        if(grids.areInputAndOutputGridsIdentical(sample))
            return sample.output
        failReason += "grids have same dimension |"
    }

    let solution

    if(columns.areInputAndOutputColumnsOfTheSameSize(sample)) {
        solution = columns.processInputAndOutputHavingColumnsOfTheSameSize(sample)
        if (solution) return sample.output
        failReason += "input and output columns have same size |"
    }

    if(rows.areInputAndOutputRowsOfTheSameSize(sample)) {
        solution = rows.processInputAndOutputHavingRowsOfTheSameSize(sample)
        if (solution) return sample.output;
        failReason += "input and output rows have the same size |"
    }

    // Now we know rows and columns are different
    if(rows.isTheOutputOneRowHigh(sample)) {
        if(columns.areThereMoreInputColumnsThanOutputColumns(sample)) {
            sample.input = grids.dedupColumns(sample.input);
            solution = rows.processInputAndOutputHavingRowsOfTheSameSize(sample);
            if(solution) return sample.output;
        }
        failReason += "output is one row high |"
    }

    if(columns.isTheOutputOneColumnWide(sample)) {
        if(rows.areThereMoreInputRowsThanOutputRows(sample)) {
            sample.input = grids.dedupRows(sample.input);
            solution = columns.processInputAndOutputHavingColumnsOfTheSameSize(sample);
            if(solution) return sample.output;
        }
        failReason += "output is one column wide |"
    }

    return "no solution"  + failReason
}

function solve_task(task, training_sample) {
    let err = sanityCheck(task)
    if(err !== 'sane') return err

    if(training_sample)
        return solve_sample(task.train[training_sample-1])

    return solve_sample(task.test[0])
}
exports.solveTask = solve_task;
