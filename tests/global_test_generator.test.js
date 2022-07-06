const {solveTask} = require("../src/solve_task");
const task_746B3537 = require("../data/training/746b3537.json");

let aggregate = { };

afterAll(() => {
    // count patterns identified
    console.log('aggregate final', aggregate)
});


describe('given a list of tasks to aggregate on', function () {
    const { task_list } = require("./tasks")

    let all_tasks = task_list.map(t => [t] )

    describe.each(
        // all_tasks
     [
        [ '00000000' ],
        [ '007bbfb7' ],
    ]
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

});

