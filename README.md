# A study on the Abstraction and Reasoning Corpus (ARC)

[![GitHub](https://img.shields.io/github/license/dereklarson/arc_study?style=for-the-badge)](https://github.com/dereklarson/arc_study/blob/master/LICENSE)
[![Generic badge](https://img.shields.io/badge/python-3.10-blue?style=for-the-badge)](https://shields.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/dereklarson/arc_study?style=for-the-badge)](https://github.com/dereklarson/arc_study/graphs/contributors)

This work is an exploration of concepts related to visual perception and cognition, based on the [ARC dataset](https://github.com/fchollet/ARC).
ARC is one of the simplest, well-defined means of demonstrating the distance between human and artificial cognition.
Despite being a set of visual tasks with at most 10 colors and a 30x30 grid, contemporary systems are poor at solving them while a human child would have minimal difficulty.

The primary goal of the work is to be a toy model that fosters idea generation, rather than be a deployable system.  The approach begins with a relatively blank slate, making only a few assumptions and design choices:
* There are three types of potential 'knowledge acquisition' at play, termed here as follows:
  * 'solving' is finding a solution to given ARC task.
  * 'learning' is building new higher-order, useful abstractions which can be applied across tasks.
  * 'training' is tuning parameters to improve efficiency of learning and solving.
* An ARC solution can be represented as a diagram of transformations that convert the input board to the output board.
* The core problem is learning a composable set of 'knowledge transformations' and then efficiently searching through their combinatorics to find an amenable solution.
* [Algorithmic complexity](https://en.wikipedia.org/wiki/Kolmogorov_complexity) is the primary guide of the search.
* Finding a solution can be broken down into two semi-separable parts:
  * Decomposition: building a hierarchical representation of each board.
  * Inference: finding a common process to turn input representations into output representations.
* The system should be modular towards 'core knowledge', allowing new concepts to be plugged in easily.
* For early simplicity, the learning and training are entirely manual, in order to find a viable solution architecture.
=======
A complete description of the dataset, its goals, and its underlying logic, can be found in: [On the Measure of Intelligence](https://arxiv.org/abs/1911.01547).

See [here](https://arc.dereklarson.info) for an interactive visual demonstration of the system at work.

## Code Structure

Four groups of classes comprise the codebase: 
* Organization: the backbone for storing and controlling everything.
* Representation: mostly the `Object` class, used to hierarchically represent the grids.
* Concepts: modular 'knowledge' classes, containing the known transformations of `Objects` 
* Solution: the `Solution` class and sub-components. 

### Organizational classes

There is a natural class hierarchy related to the ARC dataset, listed here from the bottom up:
* `Board`: Contains one 2D grid of data and controls the decomposition process.
* `Scene`: Represents a paired input and output `Board`, and controls linking between the input and output.
* `Task`: One "sample" from the ARC dataset, which will contain a number of `Scenes` broken into the "cases" and the "tests". The Task class controls creation of a `Solution`.
* `ARC`: Top-level class used to load the data, initiate global operations, and sub-select `Tasks`.

### Representation

Perhaps the most important class, an `Object` supports deep grid representation through a recursive hierarchy, (e.g. Object of Objects of Objects...).
Each grid is originally represented as a root `Object` that contains every point as a child `Object`. The decomposition process then introduces intermediate layers, which ideally help compress the representation.
An `Object` also intersects with the `Action` classes, which handles repetition (such as lines, rectangles, and regular tilings).

### Concepts

The 'Global Priors', assumptions about the world in terms of how objects relate and transform, are encoded in the following classes:
* `Action`: a transformation of an `Object` (e.g. translation, reflection, scaling)
   * All Actions take in and return a new Object, and may have additional arguments that are integers or another single Object.
   * Actions are organized into a relational hierarchy. General translation is a parent class to movement along a row, which is a parent to justifying along a row.
* `Process`: a means to decompose raw Objects into deeper representations

### Solution

The `Solution` class describes the rules governing a Task's solution.
It dictates the nature of the input decomposition, and contains a `Template` class identifying the common structure of the outputs.
Lastly, it contains a set of `SolutionNodes` which form a directed graph of transforms converting the input representation to the correct output.


## Applications

There are two docker applications built on top of this codebase: the visual demo and a Jupyterlab server (for dev purposes).

The visual demo (a [Streamlit app](https://streamlit.io)) can be run locally with `./run.sh streamlit` after modifying `docker/streamlit/.env` to match your local path.

Likewise, the Jupyterlab container can be started with `./run.sh jupyterlab` after altering the paths in its `docker/jupyterlab/.env` file. The container will mount your local code folder for a better dev experience.
