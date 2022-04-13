**nb_moss** is a tool that will check nbgrader student assignment submissions for collusion using Stanford's Moss.

## Requirements
```
pip install mossum graphviz
```

## Usage
```
check(String assignment_name, String course_directory = None)
```
* Call the check() function with one or two arguments.
* Note: Single argument execution will assume nbgrader_moss.py is inside the course directory.
* If moss.pl cannot be found in the course directory, a new script will be downloaded automatically

## Example command line usage:
```
python3 -c "import nb_moss; nb_moss.check('assignment1', '~/CS426')"
```
