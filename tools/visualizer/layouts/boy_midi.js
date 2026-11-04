registerLayout("Boy: TRS MIDI, in and out", {
  "title": "BOY: TRS MIDI, in and out",
  "source": "tools/visualizer/boy_blocks.py; Rev A netlist",
  "board": "n8synth (single board, rows 1-36)",
  "boardId": "n8synth-10hp",
  "revision": "drawn, not built",
  "notes": "In at the top, out below. The buffer on a breakout.",
  "stages": [
    {
      "id": 1,
      "name": "TRS MIDI, in and out",
      "desc": "In at the top, out below. The buffer on a breakout.",
      "test": "Not built: checked against Rev A's netlist.",
      "color": "#c8202f"
    }
  ],
  "ics": [
    {
      "id": "U1002",
      "value": "H11L1",
      "label": "H11L1",
      "stage": 1,
      "pins": [
        {
          "n": 1,
          "r": 3,
          "c": "e",
          "net": "LED cathode"
        },
        {
          "n": 2,
          "r": 4,
          "c": "e",
          "net": "MI_T"
        },
        {
          "n": 3,
          "r": 5,
          "c": "e"
        },
        {
          "n": 4,
          "r": 5,
          "c": "f",
          "net": "out"
        },
        {
          "n": 5,
          "r": 4,
          "c": "f"
        },
        {
          "n": 6,
          "r": 3,
          "c": "f"
        }
      ]
    },
    {
      "id": "U1001",
      "value": "74AHCT1G125",
      "label": "74AHCT1G125",
      "stage": 1,
      "labelSide": "side",
      "pins": [
        {
          "n": 1,
          "r": 20,
          "c": "g"
        },
        {
          "n": 2,
          "r": 21,
          "c": "g",
          "net": "in"
        },
        {
          "n": 3,
          "r": 22,
          "c": "g"
        },
        {
          "n": 4,
          "r": 23,
          "c": "g",
          "net": "out"
        },
        {
          "n": 5,
          "r": 24,
          "c": "g",
          "net": "+5VD"
        }
      ]
    }
  ],
  "twoPins": [
    {
      "id": "D1002",
      "type": "D",
      "value": "protect",
      "r1": 3,
      "c1": "b",
      "r2": 4,
      "c2": "b",
      "stage": 1
    },
    {
      "id": "R1007",
      "type": "R",
      "value": "220R",
      "r1": 8,
      "c1": "c",
      "r2": 3,
      "c2": "c",
      "stage": 1
    },
    {
      "id": "C1003",
      "type": "C",
      "value": "100n",
      "r1": 10,
      "c1": "c",
      "r2": 11,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "R1008",
      "type": "R",
      "value": "1k",
      "r1": 8,
      "c1": "g",
      "r2": 5,
      "c2": "g",
      "stage": 1
    },
    {
      "id": "R1009",
      "type": "R",
      "value": "1k",
      "r1": 5,
      "c1": "h",
      "r2": 9,
      "c2": "h",
      "stage": 1
    },
    {
      "id": "R1002",
      "type": "R",
      "value": "10k",
      "r1": 18,
      "c1": "i",
      "r2": 21,
      "c2": "i",
      "stage": 1
    },
    {
      "id": "R1001",
      "type": "R",
      "value": "1k",
      "r1": 26,
      "c1": "h",
      "r2": 21,
      "c2": "h",
      "stage": 1
    },
    {
      "id": "R1003",
      "type": "R",
      "value": "100R",
      "r1": 23,
      "c1": "h",
      "r2": 28,
      "c2": "h",
      "stage": 1
    },
    {
      "id": "R1004",
      "type": "R",
      "value": "100R",
      "r1": 28,
      "c1": "i",
      "r2": 30,
      "c2": "i",
      "stage": 1
    },
    {
      "id": "R1005",
      "type": "R",
      "value": "100R",
      "r1": 24,
      "c1": "h",
      "r2": 32,
      "c2": "h",
      "stage": 1
    },
    {
      "id": "R1006",
      "type": "R",
      "value": "100R",
      "r1": 32,
      "c1": "i",
      "r2": 34,
      "c2": "i",
      "stage": 1
    }
  ],
  "jumpers": [
    {
      "id": "W1",
      "r1": 4,
      "c1": "ctrlLi",
      "r2": 4,
      "c2": "a",
      "label": "MIDI IN T",
      "stage": 1
    },
    {
      "id": "W2",
      "r1": 8,
      "c1": "ctrlLi",
      "r2": 8,
      "c2": "a",
      "label": "MIDI IN R",
      "stage": 1
    },
    {
      "id": "W3",
      "r1": 9,
      "c1": "ctrlLi",
      "r2": 10,
      "c2": "a",
      "label": "MIDI IN S",
      "stage": 1
    },
    {
      "id": "W4",
      "r1": 33,
      "c1": "ctrlRi",
      "r2": 30,
      "c2": "j",
      "label": "MIDI OUT T",
      "stage": 1
    },
    {
      "id": "W5",
      "r1": 34,
      "c1": "ctrlRi",
      "r2": 34,
      "c2": "j",
      "label": "MIDI OUT R",
      "stage": 1
    }
  ],
  "powerWires": [],
  "jpsWires": [
    {
      "id": "J1001.3",
      "ref": "J1001",
      "pad": "3",
      "label": "MIDI IN T",
      "lbl": "MIDI IN T",
      "row": 4,
      "col": "ctrlLo",
      "stage": 1
    },
    {
      "id": "J1001.4",
      "ref": "J1001",
      "pad": "4",
      "label": "MIDI IN R",
      "lbl": "MIDI IN R",
      "row": 8,
      "col": "ctrlLo",
      "stage": 1
    },
    {
      "id": "J1001.5",
      "ref": "J1001",
      "pad": "5",
      "label": "MIDI IN S",
      "lbl": "MIDI IN S",
      "row": 9,
      "col": "ctrlLo",
      "stage": 1
    },
    {
      "id": "J1001.1",
      "ref": "J1001",
      "pad": "1",
      "label": "MIDI OUT T",
      "lbl": "MIDI OUT T",
      "row": 33,
      "col": "ctrlRo",
      "stage": 1
    },
    {
      "id": "J1001.2",
      "ref": "J1001",
      "pad": "2",
      "label": "MIDI OUT R",
      "lbl": "MIDI OUT R",
      "row": 34,
      "col": "ctrlRo",
      "stage": 1
    }
  ],
  "netLabels": [
    {
      "r": 8,
      "side": "R",
      "name": "+3V3D",
      "stage": 1
    },
    {
      "r": 9,
      "side": "R",
      "name": "MIDI_RX",
      "stage": 1
    },
    {
      "r": 18,
      "side": "R",
      "name": "+3V3D",
      "stage": 1
    },
    {
      "r": 26,
      "side": "R",
      "name": "MIDI_TX",
      "stage": 1
    },
    {
      "r": 24,
      "side": "R",
      "name": "+5VD",
      "stage": 1
    }
  ],
  "boySteps": [
    {
      "net": "MI_T",
      "line": "MI_T         J1001 tip, D1002, U1002.2",
      "rows": [
        "4L"
      ],
      "ctrl": [
        "4L"
      ],
      "parts": [
        "D1002",
        "J1001",
        "U1002"
      ],
      "wires": [
        "W1"
      ],
      "holes": [
        [
          4,
          "b"
        ],
        [
          4,
          "e"
        ],
        [
          4,
          "ctrlLo"
        ]
      ]
    },
    {
      "net": "MI_R",
      "line": "MI_R         J1001 ring, R1007 220R",
      "rows": [
        "8L"
      ],
      "ctrl": [
        "8L"
      ],
      "parts": [
        "J1001",
        "R1007"
      ],
      "wires": [
        "W2"
      ],
      "holes": [
        [
          8,
          "c"
        ],
        [
          8,
          "ctrlLo"
        ]
      ]
    },
    {
      "net": "Net-(D1002-K)",
      "line": "opto in      R1007, D1002, U1002.1",
      "rows": [
        "3L"
      ],
      "ctrl": [],
      "parts": [
        "D1002",
        "R1007",
        "U1002"
      ],
      "wires": [],
      "holes": [
        [
          3,
          "b"
        ],
        [
          3,
          "c"
        ],
        [
          3,
          "e"
        ]
      ]
    },
    {
      "net": "MI_S",
      "line": "MI_S         J1001 sleeve, C1003 100n",
      "rows": [
        "10L"
      ],
      "ctrl": [
        "9L"
      ],
      "parts": [
        "C1003",
        "J1001"
      ],
      "wires": [
        "W3"
      ],
      "holes": [
        [
          10,
          "c"
        ],
        [
          9,
          "ctrlLo"
        ]
      ]
    },
    {
      "net": "Net-(R1008-Pad2)",
      "line": "opto out     U1002.4, R1008 \u2192 +3V3D, R1009",
      "rows": [
        "5R"
      ],
      "ctrl": [],
      "parts": [
        "R1008",
        "R1009",
        "U1002"
      ],
      "wires": [],
      "holes": [
        [
          5,
          "g"
        ],
        [
          5,
          "h"
        ],
        [
          5,
          "f"
        ]
      ]
    },
    {
      "net": "MIDI_RX",
      "line": "MIDI_RX      R1009, J101 \u2192 the module",
      "rows": [
        "9R"
      ],
      "ctrl": [],
      "parts": [
        "R1009"
      ],
      "wires": [],
      "holes": [
        [
          9,
          "h"
        ]
      ]
    },
    {
      "net": "MIDI_TX",
      "line": "MIDI_TX      J101 \u2190 the module, R1001",
      "rows": [
        "26R"
      ],
      "ctrl": [],
      "parts": [
        "R1001"
      ],
      "wires": [],
      "holes": [
        [
          26,
          "h"
        ]
      ]
    },
    {
      "net": "Net-(R1001-Pad2)",
      "line": "buffer in    R1001, R1002, U1001.2",
      "rows": [
        "21R"
      ],
      "ctrl": [],
      "parts": [
        "R1001",
        "R1002",
        "U1001"
      ],
      "wires": [],
      "holes": [
        [
          21,
          "i"
        ],
        [
          21,
          "h"
        ],
        [
          21,
          "g"
        ]
      ]
    },
    {
      "net": "Net-(D1001-COM)",
      "line": "buffer out   U1001.4, R1003",
      "rows": [
        "23R"
      ],
      "ctrl": [],
      "parts": [
        "R1003",
        "U1001"
      ],
      "wires": [],
      "holes": [
        [
          23,
          "h"
        ],
        [
          23,
          "g"
        ]
      ]
    },
    {
      "net": "MO_T",
      "line": "MO_T         R1004, J1001 tip",
      "rows": [
        "30R"
      ],
      "ctrl": [
        "33R"
      ],
      "parts": [
        "J1001",
        "R1004"
      ],
      "wires": [
        "W4"
      ],
      "holes": [
        [
          30,
          "i"
        ],
        [
          33,
          "ctrlRo"
        ]
      ]
    },
    {
      "net": "MO_R",
      "line": "MO_R         R1006, J1001 ring",
      "rows": [
        "34R"
      ],
      "ctrl": [
        "34R"
      ],
      "parts": [
        "J1001",
        "R1006"
      ],
      "wires": [
        "W5"
      ],
      "holes": [
        [
          34,
          "i"
        ],
        [
          34,
          "ctrlRo"
        ]
      ]
    }
  ]
});
