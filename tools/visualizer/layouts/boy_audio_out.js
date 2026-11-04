registerLayout("Boy: Audio out, channel 1", {
  "title": "BOY: Audio out, channel 1",
  "source": "tools/visualizer/boy_blocks.py; Rev A netlist",
  "board": "n8synth (single board, rows 1-36)",
  "boardId": "n8synth-10hp",
  "revision": "drawn, not built",
  "notes": "Two poles, between the codec and the jack. The PCM3060 on a breakout.",
  "stages": [
    {
      "id": 1,
      "name": "Audio out, channel 1",
      "desc": "Two poles, between the codec and the jack. The PCM3060 on a breakout.",
      "test": "Not built: checked against Rev A's netlist.",
      "color": "#c8202f"
    }
  ],
  "ics": [
    {
      "id": "U301",
      "value": "PCM3060",
      "label": "PCM3060",
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
          "c": "e"
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
          "r": 9,
          "c": "e"
        },
        {
          "n": 10,
          "r": 10,
          "c": "e"
        },
        {
          "n": 11,
          "r": 11,
          "c": "e"
        },
        {
          "n": 12,
          "r": 12,
          "c": "e"
        },
        {
          "n": 13,
          "r": 13,
          "c": "e"
        },
        {
          "n": 14,
          "r": 14,
          "c": "e"
        },
        {
          "n": 15,
          "r": 14,
          "c": "f"
        },
        {
          "n": 16,
          "r": 13,
          "c": "f"
        },
        {
          "n": 17,
          "r": 12,
          "c": "f"
        },
        {
          "n": 18,
          "r": 11,
          "c": "f"
        },
        {
          "n": 19,
          "r": 10,
          "c": "f",
          "net": "VOUTL-"
        },
        {
          "n": 20,
          "r": 9,
          "c": "f",
          "net": "VOUTL+"
        },
        {
          "n": 21,
          "r": 8,
          "c": "f"
        },
        {
          "n": 22,
          "r": 7,
          "c": "f"
        },
        {
          "n": 23,
          "r": 6,
          "c": "f"
        },
        {
          "n": 24,
          "r": 5,
          "c": "f"
        },
        {
          "n": 25,
          "r": 4,
          "c": "f"
        },
        {
          "n": 26,
          "r": 3,
          "c": "f"
        },
        {
          "n": 27,
          "r": 2,
          "c": "f"
        },
        {
          "n": 28,
          "r": 1,
          "c": "f"
        }
      ]
    },
    {
      "id": "U302",
      "value": "TL074H",
      "label": "TL074H",
      "stage": 1,
      "pins": [
        {
          "n": 1,
          "r": 20,
          "c": "e"
        },
        {
          "n": 2,
          "r": 21,
          "c": "e"
        },
        {
          "n": 3,
          "r": 22,
          "c": "e"
        },
        {
          "n": 4,
          "r": 23,
          "c": "e"
        },
        {
          "n": 5,
          "r": 24,
          "c": "e"
        },
        {
          "n": 6,
          "r": 25,
          "c": "e"
        },
        {
          "n": 7,
          "r": 26,
          "c": "e"
        },
        {
          "n": 8,
          "r": 26,
          "c": "f",
          "net": "out"
        },
        {
          "n": 9,
          "r": 25,
          "c": "f",
          "net": "minus"
        },
        {
          "n": 10,
          "r": 24,
          "c": "f",
          "net": "plus"
        },
        {
          "n": 11,
          "r": 23,
          "c": "f"
        },
        {
          "n": 12,
          "r": 22,
          "c": "f"
        },
        {
          "n": 13,
          "r": 21,
          "c": "f"
        },
        {
          "n": 14,
          "r": 20,
          "c": "f"
        }
      ]
    }
  ],
  "twoPins": [
    {
      "id": "R316",
      "type": "R",
      "value": "12k",
      "r1": 9,
      "c1": "h",
      "r2": 16,
      "c2": "h",
      "stage": 1
    },
    {
      "id": "R315",
      "type": "R",
      "value": "12k",
      "r1": 10,
      "c1": "g",
      "r2": 17,
      "c2": "g",
      "stage": 1
    },
    {
      "id": "C315",
      "type": "C",
      "value": "1n",
      "r1": 17,
      "c1": "i",
      "r2": 16,
      "c2": "i",
      "stage": 1
    },
    {
      "id": "R320",
      "type": "R",
      "value": "30k",
      "r1": 16,
      "c1": "j",
      "r2": 15,
      "c2": "pwrR",
      "stage": 1
    },
    {
      "id": "R319",
      "type": "R",
      "value": "30k",
      "r1": 17,
      "c1": "j",
      "r2": 26,
      "c2": "j",
      "stage": 1
    },
    {
      "id": "R318",
      "type": "R",
      "value": "1k",
      "r1": 16,
      "c1": "g",
      "r2": 24,
      "c2": "g",
      "stage": 1
    },
    {
      "id": "R317",
      "type": "R",
      "value": "1k",
      "r1": 17,
      "c1": "h",
      "r2": 25,
      "c2": "h",
      "stage": 1
    },
    {
      "id": "C314",
      "type": "C",
      "value": "100p",
      "r1": 24,
      "c1": "i",
      "r2": 23,
      "c2": "pwrR",
      "stage": 1
    },
    {
      "id": "C313",
      "type": "C",
      "value": "100p",
      "r1": 25,
      "c1": "i",
      "r2": 26,
      "c2": "i",
      "stage": 1
    },
    {
      "id": "R321",
      "type": "R",
      "value": "1k",
      "r1": 26,
      "c1": "g",
      "r2": 30,
      "c2": "g",
      "stage": 1
    }
  ],
  "jumpers": [
    {
      "id": "W1",
      "r1": 33,
      "c1": "ctrlRi",
      "r2": 30,
      "c2": "j",
      "label": "OUT 1",
      "stage": 1
    }
  ],
  "powerWires": [],
  "jpsWires": [
    {
      "id": "J311.1",
      "ref": "J311",
      "pad": "1",
      "label": "OUT 1",
      "lbl": "OUT 1",
      "row": 33,
      "col": "ctrlRo",
      "stage": 1
    }
  ],
  "netLabels": [],
  "boySteps": [
    {
      "net": "VOUTL_N",
      "line": "VOUTL_N      U301.19, R315",
      "rows": [
        "10R"
      ],
      "ctrl": [],
      "parts": [
        "R315",
        "U301"
      ],
      "wires": [],
      "holes": [
        [
          10,
          "g"
        ],
        [
          10,
          "f"
        ]
      ]
    },
    {
      "net": "VOUTL_P",
      "line": "VOUTL_P      U301.20, R316",
      "rows": [
        "9R"
      ],
      "ctrl": [],
      "parts": [
        "R316",
        "U301"
      ],
      "wires": [],
      "holes": [
        [
          9,
          "h"
        ],
        [
          9,
          "f"
        ]
      ]
    },
    {
      "net": "Net-(C315-Pad1)",
      "line": "node \u2212       R315, R317, R319, C315",
      "rows": [
        "17R"
      ],
      "ctrl": [],
      "parts": [
        "C315",
        "R315",
        "R317",
        "R319"
      ],
      "wires": [],
      "holes": [
        [
          17,
          "g"
        ],
        [
          17,
          "i"
        ],
        [
          17,
          "j"
        ],
        [
          17,
          "h"
        ]
      ]
    },
    {
      "net": "Net-(C315-Pad2)",
      "line": "node +       R316, R318, R320, C315",
      "rows": [
        "16R"
      ],
      "ctrl": [],
      "parts": [
        "C315",
        "R316",
        "R318",
        "R320"
      ],
      "wires": [],
      "holes": [
        [
          16,
          "h"
        ],
        [
          16,
          "i"
        ],
        [
          16,
          "j"
        ],
        [
          16,
          "g"
        ]
      ]
    },
    {
      "net": "Net-(U302C--)",
      "line": "U302C \u2212      R317, C313, U302.9",
      "rows": [
        "25R"
      ],
      "ctrl": [],
      "parts": [
        "C313",
        "R317",
        "U302"
      ],
      "wires": [],
      "holes": [
        [
          25,
          "h"
        ],
        [
          25,
          "i"
        ],
        [
          25,
          "f"
        ]
      ]
    },
    {
      "net": "Net-(U302C-+)",
      "line": "U302C +      R318, C314, U302.10",
      "rows": [
        "24R"
      ],
      "ctrl": [],
      "parts": [
        "C314",
        "R318",
        "U302"
      ],
      "wires": [],
      "holes": [
        [
          24,
          "g"
        ],
        [
          24,
          "i"
        ],
        [
          24,
          "f"
        ]
      ]
    },
    {
      "net": "Net-(C313-Pad2)",
      "line": "U302C out    R319, C313, R321, U302.8",
      "rows": [
        "26R"
      ],
      "ctrl": [],
      "parts": [
        "C313",
        "R319",
        "R321",
        "U302"
      ],
      "wires": [],
      "holes": [
        [
          26,
          "j"
        ],
        [
          26,
          "i"
        ],
        [
          26,
          "g"
        ],
        [
          26,
          "f"
        ]
      ]
    },
    {
      "net": "AOUT1",
      "line": "AOUT1        R321, J311 (jack)",
      "rows": [
        "30R"
      ],
      "ctrl": [
        "33R"
      ],
      "parts": [
        "J311",
        "R321"
      ],
      "wires": [
        "W1"
      ],
      "holes": [
        [
          30,
          "g"
        ],
        [
          33,
          "ctrlRo"
        ]
      ]
    }
  ]
});
