const utils = require("./utility/utils");
const _ = require('lodash')

function isArrayOfArrays(arr) {
    // console.log( arr,  arr.filter( r => !utils.isElementAnArray(r) ).length === 0 )
    return arr.filter( r => !utils.isElementAnArray(r) ).length === 0
}

function sanityCheck(task) {
    if(task === null) return 'missing task';
    if(!utils.isElementAnObject(task)) return 'task should be an object'
    if(Object.keys(task).length === 0 ) return 'task should not be an empty object'

    // sanity check training data
    if(!Object.keys(task).includes('train')) return 'task missing training data'
    if(!utils.isElementAnArray(task.train)) return 'task training data must be an array'

    let len = task.train.length;
    if(len === 0) return 'task training data must be an array of one or more objects'
    if(task.train.filter(t => !utils.isElementAnObject(t)).length > 0 )  return 'task training data array may only contain objects'

    if(task.train.filter(t => !_.has(t, 'input')).length > 0 )     return 'task training data objects missing at least one input'
    if(task.train.filter(t => !_.has(t, 'output')).length > 0 )    return 'task training data objects missing at least one output'

    if(task.train.filter(t => _.has(t, 'input') && !utils.isElementAnArray(t.input) ).length > 0 )
        return 'training inputs must be arrays'
    if(task.train.filter(t => _.has(t, 'output') && !utils.isElementAnArray(t.output) ).length > 0 )
        return 'training outputs must be arrays'

    if(task.train.filter(t => t.input.length < 1 ).length > 0 ) return 'training input arrays must have one or more elements'
    if(task.train.filter(t => t.output.length < 1 ).length > 0 ) return 'training output arrays must have one or more elements'

    if(task.train.filter(t => !isArrayOfArrays(t.input) ).length > 0 )  return 'training input array elements must be arrays'
    if(task.train.filter(t => !isArrayOfArrays(t.output) ).length > 0 )  return 'training output array elements must be arrays'

    return 'sane';
}
exports.sanityCheck = sanityCheck;
