registerLayout("Boy: Gate in, channel 1", {
  "title": "BOY: Gate in, channel 1",
  "source": "tools/visualizer/boy_blocks.py; Rev A netlist",
  "board": "n8synth (single board, rows 1-36)",
  "boardId": "n8synth-10hp",
  "revision": "drawn, not built",
  "notes": "Half an LM393. Its output goes to the module's pin.",
  "stages": [
    {
      "id": 1,
      "name": "Gate in, channel 1",
      "desc": "Half an LM393. Its output goes to the module's pin.",
      "test": "Not built: checked against Rev A's netlist.",
      "color": "#c8202f"
    }
  ],
  "ics": [
    {
      "id": "U801",
      "value": "LM393",
      "label": "LM393",
      "stage": 1,
      "pins": [
        {
          "n": 1,
          "r": 12,
          "c": "e",
          "net": "GATE_IN1"
        },
        {
          "n": 2,
          "r": 13,
          "c": "e"
        },
        {
          "n": 3,
          "r": 14,
          "c": "e",
          "net": "plus"
        },
        {
          "n": 4,
          "r": 15,
          "c": "e"
        },
        {
          "n": 5,
          "r": 15,
          "c": "f"
        },
        {
          "n": 6,
          "r": 14,
          "c": "f"
        },
        {
          "n": 7,
          "r": 13,
          "c": "f"
        },
        {
          "n": 8,
          "r": 12,
          "c": "f"
        }
      ]
    },
    {
      "id": "D801",
      "value": "BAT54S",
      "label": "BAT54S",
      "stage": 1,
      "labelSide": "left",
      "pins": [
        {
          "n": 1,
          "r": 17,
          "c": "c"
        },
        {
          "n": 2,
          "r": 18,
          "c": "c"
        },
        {
          "n": 3,
          "r": 19,
          "c": "c",
          "net": "plus"
        }
      ]
    }
  ],
  "twoPins": [
    {
      "id": "R801",
      "type": "R",
      "value": "10k",
      "r1": 20,
      "c1": "a",
      "r2": 14,
      "c2": "a",
      "stage": 1
    },
    {
      "id": "R802",
      "type": "R",
      "value": "100k",
      "r1": 14,
      "c1": "b",
      "r2": 15,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "R803",
      "type": "R",
      "value": "100k",
      "r1": 14,
      "c1": "c",
      "r2": 12,
      "c2": "c",
      "stage": 1
    },
    {
      "id": "R804",
      "type": "R",
      "value": "10k",
      "r1": 9,
      "c1": "b",
      "r2": 12,
      "c2": "b",
      "stage": 1
    }
  ],
  "jumpers": [
    {
      "id": "W1",
      "r1": 20,
      "c1": "ctrlLi",
      "r2": 20,
      "c2": "b",
      "label": "GATE 1",
      "stage": 1
    },
    {
      "id": "W2",
      "r1": 19,
      "c1": "d",
      "r2": 14,
      "c2": "d",
      "label": "clamp",
      "stage": 1
    }
  ],
  "powerWires": [],
  "jpsWires": [
    {
      "id": "J810.1",
      "ref": "J810",
      "pad": "1",
      "label": "GATE 1",
      "lbl": "GATE 1",
      "row": 20,
      "col": "ctrlLo",
      "stage": 1
    }
  ],
  "netLabels": [
    {
      "r": 9,
      "side": "L",
      "name": "+3V3D",
      "stage": 1
    },
    {
      "r": 12,
      "side": "L",
      "name": "GATE_IN1",
      "stage": 1
    }
  ],
  "boySteps": [
    {
      "net": "GIN1",
      "line": "GIN1         J810 (jack), R801 10k",
      "rows": [
        "20L"
      ],
      "ctrl": [
        "20L"
      ],
      "parts": [
        "J810",
        "R801"
      ],
      "wires": [
        "W1"
      ],
      "holes": [
        [
          20,
          "a"
        ],
        [
          20,
          "ctrlLo"
        ]
      ]
    },
    {
      "net": "Net-(D801-COM)",
      "line": "U801A +      R801, D801 BAT54S, R802 100k, R803 100k, U801.3",
      "rows": [
        "14L",
        "19L"
      ],
      "ctrl": [],
      "parts": [
        "D801",
        "R801",
        "R802",
        "R803",
        "U801"
      ],
      "wires": [
        "W2"
      ],
      "holes": [
        [
          14,
          "a"
        ],
        [
          14,
          "b"
        ],
        [
          14,
          "c"
        ],
        [
          14,
          "e"
        ],
        [
          19,
          "c"
        ]
      ]
    },
    {
      "net": "GATE_IN1",
      "line": "GATE_IN1     U801.1, R803, R804 10k \u2192 +3V3D, Teensy pin 2",
      "rows": [
        "12L"
      ],
      "ctrl": [],
      "parts": [
        "R803",
        "R804",
        "U801"
      ],
      "wires": [],
      "holes": [
        [
          12,
          "c"
        ],
        [
          12,
          "b"
        ],
        [
          12,
          "e"
        ]
      ]
    }
  ]
});
