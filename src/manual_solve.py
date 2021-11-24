#!/usr/bin/python
'''
Student name(s): Ahmed Aboelala
Student ID(s): 21252201 
GitHub Repository URL: https://github.com/ahmedphcsc/ARC
'''

import os, sys
import json
import numpy as np
import re

### YOUR CODE HERE: write at least three functions which solve
### specific tasks by transforming the input x and returning the
### result. Name them according to the task ID as in the three
### examples below. Delete the three examples. The tasks you choose
### must be in the data/training directory, not data/evaluation. 


'''
The provided 2d array with cells values is either 0's or a set of single 
value z > 0, some of these z values are gathered together making a shape of square or 
rectangle with an attached cell or two distorting the shape, and some other z values 
scattered randomply in the main 2d array X.

Requirements: The task is to eliminate these random cells and clean the shape from the bad or 
noisy cells.

Solution: The implemented function loops over the 2d array and counts the four 
surounding cells of each cell only if the surounding cell has the value z > 0. 
If the cell has less than 2 heighbors with z value then it is a noisy and its value
updated to 0 in X and then X is returned with same initial shape. 
'''
def solve_7f4411dc(x):
    rows, cols = x.shape
    print(rows, cols)
    for i in range(rows):  
        for j in range(cols):
            if x[i][j] > 0:  
                count = 0
                if j < cols-1:            # check the right limit of the 2d array  
                    if x[i][j+1] > 0:     # check right neighbor cell value is z >0
                        count +=1
                        
                if j > 0:                 # check the left limit of the 2d array  
                    if x[i][j-1] > 0:
                        count +=1
                        
                if i < rows-1:            # check the lower limit of the 2d array  
                    if x[i+1][j] > 0:
                        count +=1
                        
                if i > 0:                 # check the uper limit of the 2d array
                    if x[i-1][j] > 0:
                        count +=1
                        
                if count < 2:             # check if the cell is a noisy cell 
                    x[i][j] = 0           # update cell value to be removed                   
        
    return x

'''
This task provides 2d array with cells values either 0's or 2's (base cells) 
or 8's (bridge cells), cells with 2 values are exactly 8 cells gathered together in two different 
sections in the grid each with 4 cells shaping two squares.
Cells with value 8 are either connected to each other connecting the two squares 
valued '2' cells, or not connecting them or randomly scattered in the grid.

Requirements: Identify if there is a connection from the two squares of valued '2'
cells through the cells valued 8. if there is a connection then a single cell
with value 8 is returned, if no a single cell of value 0 is returned. 

Solution: The implemented function loops over the 2d array and creates a map (dict)
of each cell as a key and its non zero valued surounding cells.
Then loops over the map keys and values to delete useless edges and cells found 
in the fake edges set.
Then check if the map containd 2 base cells that are not adjacent then return a 
single cell with value 8 other wise return a cell with 0 value.
'''
def solve_239be575(x):
    rows, cols = x.shape
    vEdge = {}                      # initiate a map of cell as key and list 4 surounding cells as edges
    fEdges=set()                     # initiate a map of fake edges 
    for i in range(rows):
        for j in range(cols):
            value= x[i][j]          # value of the current cell
            if value > 0:           # only cells values > 0 are considred  
                v = str(i)+'_'+str(j)+'-'+str(x[i][j])                  # cell given value of its index and value (i_j-value) 
                if not vEdge.keys().__contains__(v):                    # if cell not in map
                    vEdge[v]=[]                                         # initiate the cell in the map
                    if j < cols-1:                                      # check of the right limit of X
                        adjcVal = x[i][j+1]                             # get right heighbor cell value
                        if adjcVal>0 and not (value==2 and adjcVal==2):     # consider adjacent cells valued > 0 and skip adjacent cell valued 2 if the current cell is valued 2. 
                            edge = str(i)+'_'+str(j+1)+'-'+str(adjcVal)     # value of the edge in the map same as cell name
                            vEdge[v].append(edge)                           # include edge to cell values in the map
                    
                    if j > 0:                                               # check the left limit of X
                        adjcVal = x[i][j-1]                             
                        if adjcVal>0 and not (value==2 and adjcVal==2):     # check to include edge or not
                            edge = str(i)+'_'+str(j-1)+'-'+str(adjcVal)     # get left heighbor edge
                            vEdge[v].append(edge)                           # include edge to cell values in the map
                            
                    if i < rows-1:                                          # check the top limit of X
                        adjcVal = x[i+1][j]                                 # get upper heighbor edge
                        if adjcVal>0 and not (value==2 and adjcVal==2):     # check include edge or not
                            edge = str(i+1)+'_'+str(j)+'-'+str(adjcVal)
                            vEdge[v].append(edge)
                            
                    if i > 0:                                               # check of the down limit of X
                        adjcVal = x[i-1][j]
                        if adjcVal>0 and not (value==2 and adjcVal==2):     # check to include it or not as edge
                            edge = str(i-1)+'_'+str(j)+'-'+str(adjcVal)
                            vEdge[v].append(edge)
                            
                    if len(vEdge[v]) ==0:  # check if cell has no edges 
                        del vEdge[v]       # then remove its key from the map
                    elif len(vEdge[v]) == 1 and value==8 and vEdge[v][0].find('-8')>0:  # check if the cell is a bridge cell and has only one connection edge to an edge cell
                        fEdges.add(v)             # add it to the cell to edges set
                        fEdges.add(vEdge[v][0])   # add it to the edge to fake edges set                                        
                        del vEdge[v]              # remove from the map, as bridge cells has at least two edges
                    elif len(vEdge[v]) == 1 and value==2 and vEdge[v][0].find('-2')>0:  # check if the cell is a base cell and has only one connection edge to a base cell
                        fEdges.add(v)             # add it to the cell to fake edges set
                        fEdges.add(vEdge[v][0])   # add it to the edge to fake edges set    
                        del vEdge[v]              # remove cell from the map, as we need only base cells connected to bridge cells
    
    vEdge2 = {}         # new map to be updated with refined cells and edges key-value maps
    for k in vEdge.keys():
        for e in vEdge.get(k):
            if not fEdges.__contains__(e):  # check if an edge is not in the fake edges set
                if vEdge2.get(k) is None:   
                    vEdge2[k] = [e]         # create an entry for the cell in the new map and add the edge to its list value
                else:
                    vEdge2.get(k).append(e) # if cell key is created then append to its list value 
        if vEdge2.__contains__(k) and len(vEdge2.get(k)) <= 1:  # if after refinement the cell has one edge then it is useless
            del vEdge2[k]                                       # delete cell if has less than 2 edges
              
    # now will search in the refined map for a base cells values 2 and add their indexes (i,j) in a list        
    baseCells = []
    for k in vEdge2.keys():
        if k.find('-2')>0:                  # check if a key is a base cell
            ij = k.split('-')[0].split('_')
            pos = ij[0], ij[1]
            baseCells.append(pos)           # add base cell position to list as tubles
        for e in vEdge2.get(k):
            if e.find('-2')>0:              # check if an edge value is a base cell
                ij = e.split('-')[0].split('_')
                pos = ij[0], ij[1]
                baseCells.append(pos)       # add base cell position to list as 
        
    x = np.zeros((1,1), dtype=int)          # initiate a single cell with value 0
    for s in baseCells:                     # loop over the base list.
        for s1 in baseCells:
            if int(s[0]) - int(s1[0]) >1 or int(s[1]) - int(s1[1]) >1:  # check if there are two base cells not adjacent
                x[0,0]=8    # if found they there is a path from the two base sections, update the cell to value 8
    
    return x

'''
The input matrix (2d array) contian cells of 0's and some cells of a single number b > 0
A list of adjacent cells with values > 0 surounding a square of nxn of 0 values as borders, 
if the square (sub-matrix) is fully surounded with values > 0 then it is transformed 
to square of values = 3 (green), if there are any value in the border = 0 then the 
square is not fully isolated and the sub-matrix values will be = 4 (yello) and the 
cells with 0's in the border is updated to 4.

Solution scans the  matrix by looping over the squares (sub-matricies) to identify wheither
it is fully isolated or not.
1. It identify the shape of the inner matricies to loop over them per step.
2. Slice each sub-matrix in X.
3. Then slice the left, right most columns and top, down most rows (borders) if exists.  
4. Then check if these borders index values are all of values > 0.
5. If all border index values > 0 then the 0's in the sub-matrix is updated to 3.
6. If any of the border index values = 0 then the 0's in the sub-matrix is updated to 4.
7. When this loop is done, a final separate loop is performed to update the values in the 
border cells to 4 which will be the only remaing cells with values 0.  

is fully surounded with values > 0  
'''
def solve_83302e8f(x):
    rows, cols = x.shape
    
    y = []
    # Get the left upper most sub-matrix with borders to identify
    # the shape of inner-matrices
    for i in range(rows):
        y = x[0:i, 0:i]
        if np.sum(y) == 0:
            continue
        else:
            break
    
    y = np.array(y)
    n,m = y.shape    # shape of the inner matrices
    borderVal = y[n-1, m-1] # The value of the border cells
    
    mStep = m
    nStep = n
    for i in range(0,rows, nStep):         # looping over X rows with n steps 
        mStep = m
        nStep = n
        if i+n > rows:                     # update the step before the last step down (ground) of X
            nStep -=1
        for j in range(0,cols, mStep):     # looping over X rows with m steps 
            if j+m > cols:                 # update the step before the right most step of X
                mStep -= 1
                
            z = i    
            k = j    
            if j != 0:
                k = j-1                    # include the left most column into the inner-matrix scanned
            if i != 0:
                z = i-1                    # include the upper most row into the inner-matrix scanned
                
            y = x[z:i+nStep, k:j+mStep]    # inner-matrix to be scanned
                
            yRows, yCols = y.shape         # Shape for the inner matrix
                                           # initiate border arrays
            lmb = []
            rmb = []
            gb = []
            upb = []
            border = []
            if j != 0:
                lmb = y[0:yRows, 0]
                border = np.append(lmb, border) # Add left most column values to border
            
            if i != 0:
                upb = y[0, 0:yCols]
                border = np.append(upb, border) # Add upper row values to border
            
            if j+yCols < cols:
                rmb = y[0:yRows, yCols-1]
                border = np.append(rmb, border) # Add right most column values to border
                
            if i+yRows < rows:
                gb = y[yRows-1, 0:yCols]
                border = np.append(gb, border) # Add ground row values to border
            
            flag = False
            # Set flag to true if all border values are = to border value 
            for b in border:
                if b == borderVal:
                    flag = True
                    continue
                else:
                    flag = False
                    break
            
            rmCol = mStep-1 # to skip replacing right most column in the middle of the X
            grRow = nStep-1 # to skip the ground in the middle of X
            if mStep < m:
                rmCol = mStep  # include the right most column at the right border of X
            if nStep < n:
                grRow = nStep # include the ground at the last row in the matrix X
                
            if flag:
                x[i:i+grRow, j:j+rmCol] = 3 # The matrix is fully isolated
            else:
                x[i:i+grRow, j:j+rmCol] = 4 # The matrix is not fully isolated
                
    # To color the 0 values in the borders it self.        
    for i in range(rows):
        for j in range(cols):         
            if x[i,j] == 0:
                x[i,j] = 4
            
    return x

def main():
    # Find all the functions defined in this file whose names are
    # like solve_abcd1234(), and run them.

    # regex to match solve_* functions and extract task IDs
    p = r"solve_([a-f0-9]{8})" 
    tasks_solvers = []
    # globals() gives a dict containing all global names (variables
    # and functions), as name: value pairs.
    for name in globals(): 
        m = re.match(p, name)
        if m:
            # if the name fits the pattern eg solve_abcd1234
            ID = m.group(1) # just the task ID
            solve_fn = globals()[name] # the fn itself
            tasks_solvers.append((ID, solve_fn))

    for ID, solve_fn in tasks_solvers:
        # for each task, read the data and call test()
        directory = os.path.join("..", "data", "training")
        json_filename = os.path.join(directory, ID + ".json")
        data = read_ARC_JSON(json_filename)
        test(ID, solve_fn, data)
    
def read_ARC_JSON(filepath):
    """Given a filepath, read in the ARC task data which is in JSON
    format. Extract the train/test input/output pairs of
    grids. Convert each grid to np.array and return train_input,
    train_output, test_input, test_output."""
    
    # Open the JSON file and load it 
    data = json.load(open(filepath))

    # Extract the train/test input/output grids. Each grid will be a
    # list of lists of ints. We convert to Numpy.
    train_input = [np.array(data['train'][i]['input']) for i in range(len(data['train']))]
    train_output = [np.array(data['train'][i]['output']) for i in range(len(data['train']))]
    test_input = [np.array(data['test'][i]['input']) for i in range(len(data['test']))]
    test_output = [np.array(data['test'][i]['output']) for i in range(len(data['test']))]

    return (train_input, train_output, test_input, test_output)


def test(taskID, solve, data):
    """Given a task ID, call the given solve() function on every
    example in the task data."""
    print(taskID)
    train_input, train_output, test_input, test_output = data
    print("Training grids")
    for x, y in zip(train_input, train_output):
        yhat = solve(x)
        show_result(x, y, yhat)
    print("Test grids")
    for x, y in zip(test_input, test_output):
        yhat = solve(x)
        show_result(x, y, yhat)

        
def show_result(x, y, yhat):
    print("Input")
    print(x)
    print("Correct output")
    print(y)
    print("Our output")
    print(yhat)
    print("Correct?")
    if y.shape != yhat.shape:
        print(f"False. Incorrect shape: {y.shape} v {yhat.shape}")
    else:
        print(np.all(y == yhat))


if __name__ == "__main__": main()

