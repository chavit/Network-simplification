# network-simplification
Code for the "New Network Simplification Algorithms: A Tradeoff Between Simplicity and Capacity" paper. Subdirectories hold various graph topologies used in the evaluation study in the paper.

### Dependencies
The code should be run with Python 2.7. It requires `numpy`, `networkx`, and `python-louvain` Python packages (the latter with version not exceeding 0.9) that can be installed through
```
pip install numpy networkx 'python-louvain<0.9'
```

### Running the code

To reproduce Table 1, Table 2, and Figure 3 run
```
python main.py dir
```
where `dir` is a directory with topology graphs. The resulting data will be written into the file `dir.results` 

Example of `dir`.results:
```
...
16\_0\_25\_cap10
% Table 1 values
& 194 & 896 & 4930 & 2811 & 2887 & 142 & 844 & 143 & 845 & 132 & 750 & 141 & 782 \\
% Table 2 values
& 194 & 896 & 86 & 788 & 3.34 & 87 & 789 & 3.07 & 75 & 433 & 1.80 & 72 & 434 & 2.70 \\
% Figure 3 lines
0 0.570 0.586 0.570 0.586
1 0.570 0.586 0.570 0.586
2 0.570 0.586 0.570 0.586
3 0.570 0.586 0.570 0.586
4 0.570 0.586 0.570 0.586
5 0.570 0.586 0.570 0.586
6 0.570 0.586 0.570 0.586
7 0.570 0.586 0.570 0.586
...
122 nan nan 1.033 0.993
123 nan nan 1.075 1.083
124 nan nan 1.075 1.187
125 nan nan 1.198 1.355
126 nan nan 1.199 1.536
127 nan nan 1.435 1.537
...
```
