Here's a more complicated example

1: [E:2, S:3]
2: [W:1]
3: [N:1, E:4]
4: [W:3, N: 5]
5: [S:4, E:9]
6: [S:7]
7: [N:6, E:8]
8: [W:7, N:9]
9: [W:5, S:8]

```
6
|   1 -- 2  5---9
|   |       |   |
|   3 ----- 4   |
|               |
7---------------8
```

Here's my desired X/Y coords

1: (2, 0)
2: (3, 0)
3: (2, -1)
4: (4, -1)
5: (4, 0)
6: (1, 1)
7: (1, -2)
8: (5, -2)
9: (5, 0)

This issue is visually the map drawer I'm using draws a line like this from the rooms

6
|
1
|
3
|
7

The rooms aren't overlapping, but visually it looks like if you go south from 6 you'll be in 1, but actually you'll be in 7.
