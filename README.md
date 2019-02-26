# CodePoints
Python Flask backend + Pure JavaScript frontend game to test a users programming proficiency 

Built using [amcpeake/PyDE](https://github.com/amcpeake/PyDE)

Live demo coming soon

## Getting Started
As the description suggests, to be able to run CodePoints you need to have the docker edition of [PyDE](https://github.com/amcpeake/PyDE) installed.

You'll also need to set the IP address of the server running CodePoints in [codepoints.html in the IPADDRESS global variable](https://github.com/amcpeake/CodePoints/blob/master/templates/codepoints.html#L44).
You should not need any additional configuration given you correctly followed the PyDE installation instructions.

## Run CodePoints
To start CodePoints, simply run:

```python3.6 app.py```

## Adding your own challenges
Using the given challenges in [challenges.json](https://github.com/amcpeake/CodePoints/blob/master/challenges.json) as a template, you can create your own challenges.

### Name (Mandatory)
Each challenge must have a name. This is simply what the user sees in their challenge list.

i.e. "Challenge ∞: Solving P vs NP"

### Description (Mandatory)
The challenge description is given to the user as a means of describing the goal of the challenge.

This might include sample i/o, restrictions, expected types, or a hint.

i.e. "Two outputs, a and b, will be provided to your program. Take these values and print their sum"

### Languages (Mandatory)
Languages is a list of available programming languages the challenge can be written in. 

If the challenge can be written in any language, simply use "any"

i.e. "Python3"

### Codebase (Optional)
For any language, you may provide base code (i.e. "codebase"). 

This is simply an incomplete sample of code given to the user.

i.e. "'python': 'a = int(input())\n# Your code here:'"

### IO
IO consists of sets of input and output (hence the name)

Each input set should have a corresponding output set, however not every output set needs a corresponding input set.

#### Input
Input is sets of integers, strings, objects, etc. that will be passed into the user's code. 

Each set is passed in one at a time, and the resulting output is captured.

i.e. "[1, 2], [6, 5], [10, 20]"

#### Output
Output is the ouput captured from the user's code.

If a user's program takes the previous input sets and outputs the sum, the corresponding output would be:
i.e. "[3], [11], [30]"

