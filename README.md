# A study on the Abstraction and Reasoning Corpus (ARC)

[![GitHub](https://img.shields.io/github/license/dereklarson/arc_study?style=for-the-badge)](https://github.com/dereklarson/arc_study/blob/master/LICENSE)
[![Generic badge](https://img.shields.io/badge/python-3.10-blue?style=for-the-badge)](https://shields.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/dereklarson/arc_study?style=for-the-badge)](https://github.com/dereklarson/arc_study/graphs/contributors)

This work is an exploration of concepts related to visual perception and cognition, based on the [ARC dataset](https://github.com/fchollet/ARC). See [here](https://arc.dereklarson.info) for a visual demonstration. A few of the relevant, foundational questions we might ask are:
* What forms of object representation does an intelligence require to perform general inference?
* How can we connect notions of information theory to perception?
* Can we define procedures that contribute to perception which don't require training on data?
* How might recurrence tie into perception? (e.g. reinterpreting a scene after perceiving or inferring aspects of its state)

## Code Structure

There is a class hierarchy related to the ARC dataset, listed here from the bottom up:
* `Board`: Contains one 2D grid of data and the methods to process it, notably decomposition.
* `Scene`: Represents a paired input and output `Board`, and includes the processes to 'match' across boards.
* `Task`: One "sample" from the ARC dataset, which will contain a number of `Scenes` broken into the "cases" and the "tests".
* `ARC`: Top-level class used to load the data, initiate global solving, and sub-select certain `Tasks`.

To represent the Boards, there is a critical class called `Object` which supports a recursive hierarchy, (e.g. Object of Objects of Objects...). These can also have a `Generator` which handles repetition (such as a regular tiling might leverage).

The 'Global Priors', assumptions about the world in terms of how objects relate and transform, are encoded in the following classes:
* Action: a transformation of an Object (e.g. translation, reflection, scaling)
* Process: a means to decompose raw Objects into deeper representations
* Comparison: (WIP, currently just a function) means to compare objects

## Applications

There are two docker applications built on top of this codebase: the visual demo and a Jupyterlab server (for dev purposes).

The visual demo (a [Streamlit app](https://streamlit.io)) can be run locally with `./run.sh streamlit` after modifying `docker/streamlit/.env` to match your local path.

Likewise, the Jupyterlab container can be started with `./run.sh jupyterlab` after altering the paths in its `.env` file.
