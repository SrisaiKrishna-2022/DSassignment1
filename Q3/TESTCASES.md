# Graph Query Testcases

This document lists example graphs (in adjacency list JSON format) and the expected results of the two queries:

- **HasIndependentSet(k1)**
- **HasMatching(k2)**

---

## Testcase 1 — Both Fail (k1 = k2 = 2)

- **Graph 1**
```json
{
  "A": ["B"],
  "B": ["A"]
}
```

- **Graph 2**
```json
{
  "B": ["C"],
  "C": ["B", "A"],
  "A": ["C"]
}
```
## Testcase 2 — Independent Set Pass, Matching Fail (k1 = k2 = 2)

- **Graph 1**
```json
{
  "A": ["B"], 
  "B": ["A", "C"], 
  "C": ["B"]
}
```

- **Graph 2**
```json
{
  "C": ["D"],
  "D": ["C", "A"],
  "A": ["D"]
}
```
## Testcase 3 — Both Fail (k1 = 2, k2 = 3)

- **Graph 1**
```json
{
  "A": ["B", "C"],
  "B": ["A", "C"],
  "C": ["A", "B"]
}
```

- **Graph 2**
```json
{
  "C": ["D", "E"],
  "D": ["C", "E", "A", "B"],
  "E": ["C", "D", "A", "B"],
  "A": ["D", "E"],
  "B": ["D", "E"]
}
```
## Testcase 4 — Both Fail (k1 = k2 = 4)

- **Graph 1**
```json
{
  "A": ["B"],
  "B": ["A", "C"],
  "C": ["B", "D"],
  "D": ["C"]
}
```

- **Graph 2**
```json
{
  "D": ["E"],
  "E": ["D", "F"],
  "F": ["E", "G"],
  "G": ["F", "A"],
  "A": ["G"]
}
```
## Testcase 5 — Both Fail (k1 = 7, k2 = 2)

- **Graph 1**
```json
{
  "X": ["A", "B", "C"],
  "A": ["X"],
  "B": ["X"],
  "C": ["X"]
}
```

- **Graph 2**
```json
{
  "X": ["A", "B", "C"],
  "A": ["X"],
  "B": ["X"],
  "C": ["X"]
}
```
## Testcase 6 — Independent Set Pass, Matching Fail (k1 = 3, k2 = 4)

- **Graph 1**
```json
{
  "A": ["D", "E"],
  "B": ["D"],
  "C": ["E"]
}
```

- **Graph 2**
```json
{
  "A": ["D", "E"],
  "B": ["D"],
  "C": ["E"]
}
```
## Testcase 7 — Independent Set Pass, Matching Fail (k1 = 5, k2 = 2)

- **Graph 1**
```json
{
  "X": ["A", "B", "C"],
  "A": ["X"],
  "B": ["X"],
  "C": ["X"]
}
```

- **Graph 2**
```json
{
  "X": ["D", "E"],
  "D": ["X"],
  "E": ["X"]
}
```
## Testcase 8 — Independent Set Fail, Matching Pass (k1 = 4, k2 = 3)

- Union: Path of 6 vertices

- **Graph 1**
```json
{
  "A": ["B"],
  "B": ["A", "C"],
  "C": ["B", "D"]
}
```

- **Graph 2**
```json
{
  "D": ["C", "E"],
  "E": ["D", "F"],
  "F": ["E"]
}
```