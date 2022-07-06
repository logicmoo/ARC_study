const _ = require('lodash')
const { sanityCheck } = require("./sanity_check");
const { rows } = require("./rows")
const { columns } = require("./columns")
const { grids } = require("./grids")


function solve_sample(sample) {

    let patternsDetected = {}

    if(grids.doInputAndOutputGridsHaveTheSameDimensions(sample)) {
        patternsDetected["InputAndOutputGridsHaveTheSameDimensions"] = true
        if(grids.areInputAndOutputGridsIdentical(sample)) {
            patternsDetected["InputAndOutputGridsIdentical"] = true
            patternsDetected["solution"] = sample.output
            return patternsDetected //sample.output
        }
    }

    let solution

    if(columns.areInputAndOutputColumnsOfTheSameSize(sample)) {
        patternsDetected["InputAndOutputColumnsOfTheSameSize"] = true
        //  TODO:  this has more pattern detections buried inside
        solution = columns.processInputAndOutputHavingColumnsOfTheSameSize(sample)
        if (solution) {
            patternsDetected["solution"] = sample.output
            return patternsDetected //sample.output
        }
    }

    if(rows.areInputAndOutputRowsOfTheSameSize(sample)) {
        patternsDetected["InputAndOutputRowsOfTheSameSize"] = true
        //  TODO:  this has more pattern detections buried inside
        solution = rows.processInputAndOutputHavingRowsOfTheSameSize(sample)
        if (solution) {
            patternsDetected["solution"] = sample.output
            return patternsDetected // sample.output;
        }
    }

    // Now we know rows and columns are different
    if(rows.isTheOutputOneRowHigh(sample)) {
        patternsDetected["OutputOneRowHigh"] = true
        if(columns.areThereMoreInputColumnsThanOutputColumns(sample)) {
            patternsDetected["MoreInputColumnsThanOutputColumn"] = true
            sample.input = grids.dedupColumns(sample.input);
            solution = rows.processInputAndOutputHavingRowsOfTheSameSize(sample);
            if(solution) {
                patternsDetected["solution"] = sample.output
                return patternsDetected //sample.output;
            }
        }
    }

    if(columns.isTheOutputOneColumnWide(sample)) {
        patternsDetected["OutputOneColumnWide"] = true
        if(rows.areThereMoreInputRowsThanOutputRows(sample)) {
            sample.input = grids.dedupRows(sample.input);
            solution = columns.processInputAndOutputHavingColumnsOfTheSameSize(sample);
            if(solution) {
                patternsDetected["solution"] = sample.output
                return patternsDetected //sample.output;
            }
        }
    }


    if(grids.isInputGridScaledDownByIntegerFactor(sample) ) {
        patternsDetected["InputGridScaledDownByIntegerFactor"] = true
    }

    if( grids.isInputGridScaledUpByIntegerFactor(sample) ) {

        // are there copies of the input in the  output?
        //   are they exact copies?  (in number of cells)
        //   how many are there?  what are their colors
        //   OR:  if input is scaled and overlaid on the output, do all black regions overlap all black regions?
        //    OR: if input regions are scaled and overlaid on output, what regions are no longer identical?

        patternsDetected["InputGridScaledUpByIntegerFactor"] = true
    }

    return  patternsDetected
}

function solve_task(task, training_sample) {
    let err = sanityCheck(task)
    if(err !== 'sane') return err

    if(training_sample)
        return solve_sample(task.train[training_sample-1])

    return solve_sample(task.test[0])
}
exports.solveTask = solve_task;
