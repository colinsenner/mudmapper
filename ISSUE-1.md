The issue is that an exit east may need to be spaced out more than just x+1, here's a dumb example: here's room vnums with exits to which rooms, and the map I need generated.

1: [E:2, S:3]
2: [W:1]
3: [N:1, E:4]
4: [W:3, N: 5]
5: [S:4]

```
1 -- 2  5
|       |
3 ----- 4

```

Here's their possible X/Y coords (doesn't need to be exact)

1: (0,0)
2: (1, 0)
3: (0, -1)
4: (4, -1)
5: (4, 0)

Notice how if we naively assign room 4 to (1,1) and then 5 to (1,0), it will overlap with room 2, but we can't just move 5 over to (2,0) because that would look like room 5 is NE (/ diagonal) from room 4, so we also must adjust room 4 over.
