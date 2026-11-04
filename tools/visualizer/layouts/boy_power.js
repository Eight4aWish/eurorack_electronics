registerLayout("Boy: Power", {
  "title": "BOY: Power",
  "source": "tools/visualizer/boy_blocks.py; Rev A netlist",
  "board": "n8synth (single board, rows 1-36)",
  "boardId": "n8synth-10hp",
  "revision": "drawn, not built",
  "notes": "The rails stand in for the board's own power header. One capacitor of each parallel group drawn.",
  "stages": [
    {
      "id": 1,
      "name": "Power",
      "desc": "The rails stand in for the board's own power header. One capacitor of each parallel group drawn.",
      "test": "Not built: checked against Rev A's netlist.",
      "color": "#c8202f"
    }
  ],
  "ics": [
    {
      "id": "U201",
      "value": "TPS54308",
      "label": "TPS54308",
      "stage": 1,
      "pins": [
        {
          "n": 1,
          "r": 8,
          "c": "e"
        },
        {
          "n": 2,
          "r": 9,
          "c": "e",
          "net": "SW"
        },
        {
          "n": 3,
          "r": 10,
          "c": "e",
          "net": "BUCK_VIN"
        },
        {
          "n": 4,
          "r": 10,
          "c": "f",
          "net": "FB"
        },
        {
          "n": 5,
          "r": 9,
          "c": "f",
          "net": "BUCK_EN"
        },
        {
          "n": 6,
          "r": 8,
          "c": "f"
        }
      ]
    },
    {
      "id": "U202",
      "value": "L78M05",
      "label": "L78M05",
      "stage": 1,
      "labelSide": "left",
      "pins": [
        {
          "n": 1,
          "r": 20,
          "c": "c",
          "net": "+12V"
        },
        {
          "n": 2,
          "r": 21,
          "c": "c"
        },
        {
          "n": 3,
          "r": 22,
          "c": "c",
          "net": "5VA_REG"
        }
      ]
    },
    {
      "id": "U203",
      "value": "XC6206",
      "label": "XC6206",
      "stage": 1,
      "labelSide": "left",
      "pins": [
        {
          "n": 1,
          "r": 27,
          "c": "c"
        },
        {
          "n": 2,
          "r": 28,
          "c": "c",
          "net": "3V3A_REG"
        },
        {
          "n": 3,
          "r": 29,
          "c": "c",
          "net": "+5VA"
        }
      ]
    },
    {
      "id": "U204",
      "value": "XC6206",
      "label": "XC6206",
      "stage": 1,
      "labelSide": "right",
      "pins": [
        {
          "n": 1,
          "r": 27,
          "c": "g"
        },
        {
          "n": 2,
          "r": 28,
          "c": "g",
          "net": "3V3D_REG"
        },
        {
          "n": 3,
          "r": 29,
          "c": "g",
          "net": "+5VD"
        }
      ]
    }
  ],
  "twoPins": [
    {
      "id": "D201",
      "type": "D",
      "value": "SS34",
      "r1": 2,
      "c1": "a",
      "r2": 2,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "FB201",
      "type": "L",
      "value": "ferrite",
      "r1": 2,
      "c1": "b",
      "r2": 4,
      "c2": "b",
      "stage": 1
    },
    {
      "id": "FB203",
      "type": "L",
      "value": "ferrite",
      "r1": 4,
      "c1": "c",
      "r2": 10,
      "c2": "c",
      "stage": 1
    },
    {
      "id": "C205",
      "type": "C",
      "value": "10u",
      "r1": 10,
      "c1": "b",
      "r2": 11,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "R201",
      "type": "R",
      "value": "510k",
      "r1": 10,
      "c1": "d",
      "r2": 11,
      "c2": "g",
      "stage": 1
    },
    {
      "id": "R202",
      "type": "R",
      "value": "75k",
      "r1": 9,
      "c1": "i",
      "r2": 9,
      "c2": "pwrR",
      "stage": 1
    },
    {
      "id": "L201",
      "type": "L",
      "value": "inductor",
      "r1": 9,
      "c1": "a",
      "r2": 14,
      "c2": "a",
      "stage": 1
    },
    {
      "id": "C210",
      "type": "C",
      "value": "output",
      "r1": 14,
      "c1": "c",
      "r2": 15,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "R203",
      "type": "R",
      "value": "feedback",
      "r1": 14,
      "c1": "d",
      "r2": 10,
      "c2": "g",
      "stage": 1
    },
    {
      "id": "R206",
      "type": "R",
      "value": "0R",
      "r1": 14,
      "c1": "e",
      "r2": 18,
      "c2": "e",
      "stage": 1
    },
    {
      "id": "C216",
      "type": "C",
      "value": "10u",
      "r1": 22,
      "c1": "a",
      "r2": 23,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "R207",
      "type": "R",
      "value": "0R",
      "r1": 22,
      "c1": "d",
      "r2": 25,
      "c2": "d",
      "stage": 1
    },
    {
      "id": "C219",
      "type": "C",
      "value": "1u",
      "r1": 28,
      "c1": "a",
      "r2": 31,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "R208",
      "type": "R",
      "value": "0R",
      "r1": 28,
      "c1": "d",
      "r2": 31,
      "c2": "d",
      "stage": 1
    },
    {
      "id": "C221",
      "type": "C",
      "value": "1u",
      "r1": 28,
      "c1": "h",
      "r2": 29,
      "c2": "pwrR",
      "stage": 1
    },
    {
      "id": "R209",
      "type": "R",
      "value": "0R",
      "r1": 28,
      "c1": "i",
      "r2": 31,
      "c2": "i",
      "stage": 1
    }
  ],
  "jumpers": [
    {
      "id": "W1",
      "r1": 11,
      "c1": "h",
      "r2": 9,
      "c2": "h",
      "label": "BUCK_EN",
      "stage": 1
    },
    {
      "id": "W2",
      "r1": 20,
      "c1": "a",
      "r2": 4,
      "c2": "a",
      "label": "+12V",
      "stage": 1
    },
    {
      "id": "W3",
      "r1": 29,
      "c1": "a",
      "r2": 25,
      "c2": "a",
      "label": "+5VA",
      "stage": 1
    },
    {
      "id": "W4",
      "r1": 18,
      "c1": "a",
      "r2": 29,
      "c2": "h",
      "label": "+5VD",
      "stage": 1
    }
  ],
  "powerWires": [],
  "jpsWires": [],
  "netLabels": [
    {
      "r": 4,
      "side": "L",
      "name": "+12V",
      "stage": 1
    },
    {
      "r": 18,
      "side": "L",
      "name": "+5VD",
      "stage": 1
    },
    {
      "r": 25,
      "side": "L",
      "name": "+5VA",
      "stage": 1
    },
    {
      "r": 31,
      "side": "L",
      "name": "+3V3A",
      "stage": 1
    },
    {
      "r": 31,
      "side": "R",
      "name": "+3V3D",
      "stage": 1
    }
  ],
  "boySteps": [
    {
      "net": "+12V_IN",
      "line": "+12V_IN      D201 anode, on the rail",
      "rows": [],
      "ctrl": [],
      "parts": [
        "D201"
      ],
      "wires": [],
      "holes": [
        [
          2,
          "pwrL"
        ]
      ]
    },
    {
      "net": "+12V_P",
      "line": "+12V_P       D201 cathode, FB201",
      "rows": [
        "2L"
      ],
      "ctrl": [],
      "parts": [
        "D201",
        "FB201"
      ],
      "wires": [],
      "holes": [
        [
          2,
          "a"
        ],
        [
          2,
          "b"
        ]
      ]
    },
    {
      "net": "BUCK_VIN",
      "line": "BUCK_VIN     FB203, C205, R201, U201 VIN",
      "rows": [
        "10L"
      ],
      "ctrl": [],
      "parts": [
        "C205",
        "FB203",
        "R201",
        "U201"
      ],
      "wires": [],
      "holes": [
        [
          10,
          "c"
        ],
        [
          10,
          "b"
        ],
        [
          10,
          "d"
        ],
        [
          10,
          "e"
        ]
      ]
    },
    {
      "net": "BUCK_EN",
      "line": "BUCK_EN      R201, R202, U201 EN",
      "rows": [
        "11R",
        "9R"
      ],
      "ctrl": [],
      "parts": [
        "R201",
        "R202",
        "U201"
      ],
      "wires": [
        "W1"
      ],
      "holes": [
        [
          11,
          "g"
        ],
        [
          9,
          "i"
        ],
        [
          9,
          "f"
        ]
      ]
    },
    {
      "net": "5V_BUCK",
      "line": "5V_BUCK      L201, C210, R203, R206 \u2192 +5VD",
      "rows": [
        "14L"
      ],
      "ctrl": [],
      "parts": [
        "C210",
        "L201",
        "R203",
        "R206"
      ],
      "wires": [],
      "holes": [
        [
          14,
          "a"
        ],
        [
          14,
          "c"
        ],
        [
          14,
          "d"
        ],
        [
          14,
          "e"
        ]
      ]
    },
    {
      "net": "5VA_REG",
      "line": "5VA_REG      U202 out, C216, R207 \u2192 +5VA",
      "rows": [
        "22L"
      ],
      "ctrl": [],
      "parts": [
        "C216",
        "R207",
        "U202"
      ],
      "wires": [],
      "holes": [
        [
          22,
          "a"
        ],
        [
          22,
          "d"
        ],
        [
          22,
          "c"
        ]
      ]
    },
    {
      "net": "3V3A_REG",
      "line": "3V3A_REG     U203 out, C219, R208 \u2192 +3V3A",
      "rows": [
        "28L"
      ],
      "ctrl": [],
      "parts": [
        "C219",
        "R208",
        "U203"
      ],
      "wires": [],
      "holes": [
        [
          28,
          "a"
        ],
        [
          28,
          "d"
        ],
        [
          28,
          "c"
        ]
      ]
    },
    {
      "net": "3V3D_REG",
      "line": "3V3D_REG     U204 out, C221, R209 \u2192 +3V3D",
      "rows": [
        "28R"
      ],
      "ctrl": [],
      "parts": [
        "C221",
        "R209",
        "U204"
      ],
      "wires": [],
      "holes": [
        [
          28,
          "h"
        ],
        [
          28,
          "i"
        ],
        [
          28,
          "g"
        ]
      ]
    }
  ]
});
