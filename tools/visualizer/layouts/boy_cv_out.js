registerLayout("Boy: CV out, channel 1", {
  "title": "BOY: CV out, channel 1",
  "source": "tools/visualizer/boy_blocks.py; Rev A netlist",
  "board": "n8synth (single board, rows 1-36)",
  "boardId": "n8synth-10hp",
  "revision": "drawn, not built",
  "notes": "One channel of the DAC8568, on a breakout; half of U504 makes the shared offset.",
  "stages": [
    {
      "id": 1,
      "name": "CV out, channel 1",
      "desc": "One channel of the DAC8568, on a breakout; half of U504 makes the shared offset.",
      "test": "Not built: checked against Rev A's netlist.",
      "color": "#c8202f"
    }
  ],
  "ics": [
    {
      "id": "U501",
      "value": "DAC8568",
      "label": "DAC8568",
      "stage": 1,
      "pins": [
        {
          "n": 1,
          "r": 1,
          "c": "e"
        },
        {
          "n": 2,
          "r": 2,
          "c": "e"
        },
        {
          "n": 3,
          "r": 3,
          "c": "e"
        },
        {
          "n": 4,
          "r": 4,
          "c": "e",
          "net": "DAC1"
        },
        {
          "n": 5,
          "r": 5,
          "c": "e"
        },
        {
          "n": 6,
          "r": 6,
          "c": "e"
        },
        {
          "n": 7,
          "r": 7,
          "c": "e"
        },
        {
          "n": 8,
          "r": 8,
          "c": "e"
        },
        {
          "n": 9,
          "r": 8,
          "c": "f"
        },
        {
          "n": 10,
          "r": 7,
          "c": "f"
        },
        {
          "n": 11,
          "r": 6,
          "c": "f"
        },
        {
          "n": 12,
          "r": 5,
          "c": "f"
        },
        {
          "n": 13,
          "r": 4,
          "c": "f"
        },
        {
          "n": 14,
          "r": 3,
          "c": "f"
        },
        {
          "n": 15,
          "r": 2,
          "c": "f"
        },
        {
          "n": 16,
          "r": 1,
          "c": "f"
        }
      ]
    },
    {
      "id": "U502",
      "value": "TL074H",
      "label": "TL074H",
      "stage": 1,
      "pins": [
        {
          "n": 1,
          "r": 10,
          "c": "e",
          "net": "CVDRV1"
        },
        {
          "n": 2,
          "r": 11,
          "c": "e",
          "net": "minus"
        },
        {
          "n": 3,
          "r": 12,
          "c": "e",
          "net": "DAC1"
        },
        {
          "n": 4,
          "r": 13,
          "c": "e"
        },
        {
          "n": 5,
          "r": 14,
          "c": "e"
        },
        {
          "n": 6,
          "r": 15,
          "c": "e"
        },
        {
          "n": 7,
          "r": 16,
          "c": "e"
        },
        {
          "n": 8,
          "r": 16,
          "c": "f"
        },
        {
          "n": 9,
          "r": 15,
          "c": "f"
        },
        {
          "n": 10,
          "r": 14,
          "c": "f"
        },
        {
          "n": 11,
          "r": 13,
          "c": "f"
        },
        {
          "n": 12,
          "r": 12,
          "c": "f"
        },
        {
          "n": 13,
          "r": 11,
          "c": "f"
        },
        {
          "n": 14,
          "r": 10,
          "c": "f"
        }
      ]
    },
    {
      "id": "U504",
      "value": "TL074H",
      "label": "TL074H",
      "stage": 1,
      "pins": [
        {
          "n": 1,
          "r": 18,
          "c": "e",
          "net": "OFFSET_REF"
        },
        {
          "n": 2,
          "r": 19,
          "c": "e",
          "net": "OFFSET_REF"
        },
        {
          "n": 3,
          "r": 20,
          "c": "e"
        },
        {
          "n": 4,
          "r": 21,
          "c": "e"
        },
        {
          "n": 5,
          "r": 22,
          "c": "e"
        },
        {
          "n": 6,
          "r": 23,
          "c": "e"
        },
        {
          "n": 7,
          "r": 24,
          "c": "e"
        },
        {
          "n": 8,
          "r": 24,
          "c": "f"
        },
        {
          "n": 9,
          "r": 23,
          "c": "f"
        },
        {
          "n": 10,
          "r": 22,
          "c": "f"
        },
        {
          "n": 11,
          "r": 21,
          "c": "f"
        },
        {
          "n": 12,
          "r": 20,
          "c": "f"
        },
        {
          "n": 13,
          "r": 19,
          "c": "f"
        },
        {
          "n": 14,
          "r": 18,
          "c": "f"
        }
      ]
    },
    {
      "id": "U402",
      "value": "DG412",
      "label": "DG412",
      "stage": 1,
      "pins": [
        {
          "n": 1,
          "r": 26,
          "c": "e"
        },
        {
          "n": 2,
          "r": 27,
          "c": "e"
        },
        {
          "n": 3,
          "r": 28,
          "c": "e",
          "net": "CVDRV1"
        },
        {
          "n": 4,
          "r": 29,
          "c": "e"
        },
        {
          "n": 5,
          "r": 30,
          "c": "e"
        },
        {
          "n": 6,
          "r": 31,
          "c": "e"
        },
        {
          "n": 7,
          "r": 32,
          "c": "e"
        },
        {
          "n": 8,
          "r": 33,
          "c": "e"
        },
        {
          "n": 9,
          "r": 33,
          "c": "f"
        },
        {
          "n": 10,
          "r": 32,
          "c": "f"
        },
        {
          "n": 11,
          "r": 31,
          "c": "f"
        },
        {
          "n": 12,
          "r": 30,
          "c": "f"
        },
        {
          "n": 13,
          "r": 29,
          "c": "f"
        },
        {
          "n": 14,
          "r": 28,
          "c": "f"
        },
        {
          "n": 15,
          "r": 27,
          "c": "f"
        },
        {
          "n": 16,
          "r": 26,
          "c": "f"
        }
      ]
    }
  ],
  "twoPins": [
    {
      "id": "R505",
      "type": "R",
      "value": "33k",
      "r1": 11,
      "c1": "b",
      "r2": 10,
      "c2": "b",
      "stage": 1
    },
    {
      "id": "C505",
      "type": "C",
      "value": "100p",
      "r1": 11,
      "c1": "c",
      "r2": 10,
      "c2": "c",
      "stage": 1
    },
    {
      "id": "R504",
      "type": "R",
      "value": "10k",
      "r1": 18,
      "c1": "d",
      "r2": 11,
      "c2": "d",
      "stage": 1
    }
  ],
  "jumpers": [
    {
      "id": "W1",
      "r1": 4,
      "c1": "a",
      "r2": 12,
      "c2": "a",
      "label": "DAC1",
      "stage": 1
    },
    {
      "id": "W2",
      "r1": 18,
      "c1": "a",
      "r2": 19,
      "c2": "a",
      "label": "follower",
      "stage": 1
    },
    {
      "id": "W3",
      "r1": 10,
      "c1": "a",
      "r2": 28,
      "c2": "a",
      "label": "CVDRV1",
      "stage": 1
    }
  ],
  "powerWires": [],
  "jpsWires": [],
  "netLabels": [],
  "boySteps": [
    {
      "net": "DAC1",
      "line": "DAC1         U501.4 VOUTA, U502.3 +",
      "rows": [
        "12L",
        "4L"
      ],
      "ctrl": [],
      "parts": [
        "U501",
        "U502"
      ],
      "wires": [
        "W1"
      ],
      "holes": [
        [
          4,
          "e"
        ],
        [
          12,
          "e"
        ]
      ]
    },
    {
      "net": "Net-(U502A--)",
      "line": "U502A \u2212      R504 10k, R505 33k, C505 100p, U502.2",
      "rows": [
        "11L"
      ],
      "ctrl": [],
      "parts": [
        "C505",
        "R504",
        "R505",
        "U502"
      ],
      "wires": [],
      "holes": [
        [
          11,
          "b"
        ],
        [
          11,
          "c"
        ],
        [
          11,
          "d"
        ],
        [
          11,
          "e"
        ]
      ]
    },
    {
      "net": "OFFSET_REF",
      "line": "OFFSET_REF   R504 (one per channel), U504.1, U504.2",
      "rows": [
        "18L",
        "19L"
      ],
      "ctrl": [],
      "parts": [
        "R504",
        "U504"
      ],
      "wires": [
        "W2"
      ],
      "holes": [
        [
          18,
          "d"
        ],
        [
          18,
          "e"
        ],
        [
          19,
          "e"
        ]
      ]
    },
    {
      "net": "CVDRV1",
      "line": "CVDRV1       U502.1, R505, C505, U402.3 \u2192 switch",
      "rows": [
        "10L",
        "28L"
      ],
      "ctrl": [],
      "parts": [
        "C505",
        "R505",
        "U402",
        "U502"
      ],
      "wires": [
        "W3"
      ],
      "holes": [
        [
          10,
          "b"
        ],
        [
          10,
          "c"
        ],
        [
          10,
          "e"
        ],
        [
          28,
          "e"
        ]
      ]
    }
  ]
});
