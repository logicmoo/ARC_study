const {solveTask} = require("../src/solve_task");
const task_746B3537 = require("../data/training/746b3537.json");


describe('given a list of tasks to aggregate on', function () {
    const { task_list } = require("./tasks")
    let aggregate = { };

    let all_tasks = task_list.map(t => [t] )
    console.log(all_tasks)

    describe.each( all_tasks
        //[
        // [ '00000000' ],
        // [ '007bbfb7' ],
    // ]
    )('given task_%s', (task_id) => {

        let task_file = require("../data/training/" + task_id + ".json")
        let test_samples = task_file.train.map((sample, index) => {
            // [ training sample #, training output result
            return { index: index, output: sample.output, output_string: JSON.stringify(sample.output) }
        })
        console.log('test_samples', test_samples)

        test.each(test_samples)
          (`should give the solution to training sample ($index)`, ({index, output}) => {
            //  console.log(index, output)
            let  solution =  solveTask(task_file, index + 1)
            expect(solution).toStrictEqual(output)
        });

    });

});

