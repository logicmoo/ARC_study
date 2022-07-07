const _ = require('lodash')
const { sanityCheck } = require("./sanity_check");
const { rows } = require("./rows")
const { columns } = require("./columns")
const { grids } = require("./grids")


function solve_sample(sample) {

    let patternsDetected = {}

    if(grids.doInputAndOutputGridsHaveTheSameDimensions(sample))   patternsDetected["InputAndOutputGridsHaveTheSameDimensions"] = true
    if(grids.areInputAndOutputGridsIdentical(sample)) patternsDetected["InputAndOutputGridsIdentical"] = true

    if(columns.areInputAndOutputColumnsOfTheSameSize(sample))  patternsDetected["InputAndOutputColumnsOfTheSameSize"] = true
    if(columns.doesTheOutputColumnMatchAnyColumnsOfTheInput(sample))  patternsDetected["OutputColumnMatchAnyColumnsOfTheInput"] = true
    if(columns.areAllColumnsEqual(sample.input))  patternsDetected["AllInputColumnsEqual"] = true

    if(rows.areInputAndOutputRowsOfTheSameSize(sample)) patternsDetected["InputAndOutputRowsOfTheSameSize"] = true
    if(rows.doesTheOutputRowMatchAnyRowsOfTheInput(sample))  patternsDetected["OutputRowMatchAnyRowsOfTheInput"] = true
    if(rows.areAllRowsEqual(sample.input))  patternsDetected["AllInputRowsEqual"] = true

    if(rows.isTheOutputOneRowHigh(sample))  patternsDetected["OutputOneRowHigh"] = true
    if(columns.areThereMoreInputColumnsThanOutputColumns(sample))  patternsDetected["MoreInputColumnsThanOutputColumn"] = true

    if(columns.isTheOutputOneColumnWide(sample)) patternsDetected["OutputOneColumnWide"] = true
    if(rows.areThereMoreInputRowsThanOutputRows(sample)) patternsDetected["MoreInputRowsThanOutputRows"] = true

    if(grids.isInputGridScaledDownByIntegerFactor(sample) )  patternsDetected["InputGridScaledDownByIntegerFactor"] = true
    if(grids.isInputGridScaledUpByIntegerFactor(sample) ) patternsDetected["InputGridScaledUpByIntegerFactor"] = true

    if(grids.areInputAndOutputSquare(sample)) patternsDetected["InputAndOutputSquare"] = true
    if(grids.isInputSquare(sample)) patternsDetected["InputSquare"] = true
    if(grids.isOutputSquare(sample)) patternsDetected["OutputSquare"] = true
    if(grids.areInputSquareAndOutputNotSquare(sample)) patternsDetected["InputSquareAndOutputNotSquare"] = true
    if(grids.areInputNotSquareAndOutputSquare(sample)) patternsDetected["InputNotSquareAndOutputSquare"] = true
    if(grids.areNeitherInputNorOutputSquare(sample)) patternsDetected["NeitherInputNorOutputSquare"] = true

    if(grids.areAllInputCellsBlack(sample)) patternsDetected["AllInputCellsBlack"] = true
    if(grids.areAllOutputCellsBlack(sample)) patternsDetected["AllOutputCellsBlack"] = true
    if(grids.areAllInputCellsColored(sample)) patternsDetected["AllInputCellsColored"] = true
    if(grids.areAllOutputCellsColored(sample)) patternsDetected["AllOutputCellsColored"] = true

    if(grids.areAllInputCellsTheSameColor(sample)) patternsDetected["AllInputCellsTheSameColor"] = true
    if(grids.areAllOutputCellsTheSameColor(sample)) patternsDetected["AllOutputCellsTheSameColor"] = true

    if(grids.areAllInputCellsOneColorOrBlack(sample)) patternsDetected["AllInputCellsOneColorOrBlack"] = true
    if(grids.areAllOutputCellsOneColorOrBlack(sample)) patternsDetected["AllOutputCellsOneColorOrBlack"] = true
    if(grids.areAllInputAndOutputCellsOneColorOrBlack(sample)) patternsDetected["AllInputAndOutputCellsOneColorOrBlack"] = true

    if(grids.areAllInputCellsTwoColorsOrBlack(sample)) patternsDetected["AllInputCellsTwoColorsOrBlack"] = true
    if(grids.areAllOutputCellsTwoColorsOrBlack(sample)) patternsDetected["AllOutputCellsTwoColorsOrBlack"] = true
    if(grids.areAllInputAndOutputCellsTwoColorsOrBlack(sample)) patternsDetected["AllInputAndOutputCellsTwoColorsOrBlack"] = true

    if(patternsDetected === {})  patternsDetected["NoPatternsDetected"] = true

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
