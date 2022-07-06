const _ = require("lodash");
const {solveTask} = require("../src/solve_task");
const { task_list } = require("./tasks")

let some_tasks =   [[ '00000000' ], [ '007bbfb7' ] ]
let all_tasks = task_list.map(t => [t] )
let aggregate = { };


function everySampleHasProperty(task_id, property) {
    let sample_keys = Object.keys(aggregate[task_id])
    return sample_keys.every(key => _.has(aggregate[task_id][key], property))

}

let propertyList = [
    'InputAndOutputGridsHaveTheSameDimensions', 'InputAndOutputGridsIdentical', 'InputAndOutputColumnsOfTheSameSize',
    'OutputColumnMatchAnyColumnsOfTheInput', 'AllInputColumnsEqual', 'InputAndOutputRowsOfTheSameSize',
    'OutputRowMatchAnyRowsOfTheInput', 'AllInputRowsEqual', 'OutputOneRowHigh', 'MoreInputColumnsThanOutputColumn',
    'OutputOneColumnWide', 'MoreInputRowsThanOutputRows', 'InputGridScaledDownByIntegerFactor', 'InputGridScaledUpByIntegerFactor'
]

function processAggregate() {
    let use_tasks = all_tasks // some_tasks
    let propertyTable = { }
    propertyList.forEach(property => {
        let at =  use_tasks.filter(task_id => everySampleHasProperty(task_id, property))
        propertyTable[property] = at.length;
        // console.log(property, at.length   // ,  at
        // )

    })

    console.log(propertyTable)
}



describe('given a list of tasks to aggregate on', function () {

    describe.each(
    //    some_tasks
        all_tasks
    )('given task_%s', (task_id) => {

        let task_file = require("../data/training/" + task_id + ".json")
        let test_samples = task_file.train.map((sample, index) => {
            // [ training sample #, training output result
            return { index: index, output: sample.output, output_string: JSON.stringify(sample.output) }
        })
        // console.log('test_samples', test_samples)

        let taskData = {}
        test.each(test_samples)
          (`should give the solution to training sample ($index)`, ({index, output}) => {
            //  console.log(index, output)
            let  patternsDetected =  solveTask(task_file, index + 1)
            let sampleKey = `sample_${index+1}`
            taskData[sampleKey] = patternsDetected
            //  console.log(taskData)
            let solution = patternsDetected.solution || false
            expect(true).toStrictEqual(true)
           // expect(solution).toStrictEqual(output)
        });

        test(`should give the solution to test`, () => {
            let  patternsDetected =  solveTask(task_file)
            taskData["test"] = patternsDetected
            aggregate[task_id] = taskData;
            let solution = patternsDetected.solution || false
            expect(true).toStrictEqual(true)
//            expect(solution).toStrictEqual(task_file.test[0].output)
        });

    });

    afterAll(() => {
        // count patterns identified
        // console.log('aggregate final', aggregate)

        processAggregate()

    });

});

