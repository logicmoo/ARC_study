const fs = require('fs');
const { solveTask } = require('../src/solve_task')
const task_746B3537 = require("../data/training/746b3537.json");
const path = require("path");

// this creates test files in the tests/auto/  subdirectory
// the tests in the files test a single task
// as the test files are created, wallaby should pick them up and run them

function testRequiresString() {
  return "const { solveTask } = require('../../src/solve_task')\n"
}

function taskRequireString(task_id) {
    return "const task_" +  task_id +  " = require('../../data/training/" + task_id + ".json')\n\n"
}

function taskDescribeString(task_id) {
    return "describe('given " +  task_id +  "', function () {\n\n"
}

function itTrainTests(task_id, training_sample) {
   return  "    it('should give the solution to task_"  +  task_id +   " training sample " + training_sample + "', function () {\n"
       + "       let result = solveTask(task_"  +  task_id +   ", "+ training_sample + ")\n"
       + "       console.log('result:', result)\n"
       + "       expect(result).toStrictEqual("
       +               "task_"   + task_id +   ".train[" + (training_sample-1)  +   "].output)\n"
       + "    })\n\n"

}

describe('given a list of tasks', function () {
    const { task_list } = require("./tasks")
    describe('given a task in the list of tasks', function () {


        for (let i = 0; i < 0; i++) {
        // for (let i = 0; i < 100; i++) {

            let task_id =  task_list[i];
            let task_file = require("../data/training/" + task_id + ".json")

            let test_file_contents =
                testRequiresString()
                + taskRequireString(task_id)
                + taskDescribeString(task_id)

            // Add training sections
            task_file.train.forEach((t, i) => {
                test_file_contents = test_file_contents + itTrainTests(task_id, i+1)
            })

            // task eval section (test)
            test_file_contents = test_file_contents
              +  "    // test evaluation\n"
              +  "    it('should give the solution to task_" + task_id +  "test', function () { \n"
              +  "       let result = solveTask(task_"  +  task_id +   ")\n"
              +  "       console.log('result:', result)\n"
              +  "       expect(result).toBe(task_" + task_id + ".test[0].output)\n"
              +  "    })\n\n"

            test_file_contents =  test_file_contents   + "})\n"
            fs.writeFileSync("/home/jon/js/arc/tests/auto/task_" + task_id + ".test.js", test_file_contents);

        }

        it('should always be true', function () {
            expect(true).toStrictEqual(true)
        });


    });
});
