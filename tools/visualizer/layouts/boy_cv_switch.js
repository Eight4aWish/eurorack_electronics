registerLayout("Boy: Jack switch, channel 1", {
  "title": "BOY: Jack switch, channel 1",
  "source": "tools/visualizer/boy_blocks.py; Rev A netlist",
  "board": "n8synth (single board, rows 1-36)",
  "boardId": "n8synth-10hp",
  "revision": "drawn, not built",
  "notes": "The TCA9555 on a breakout.",
  "stages": [
    {
      "id": 1,
      "name": "Jack switch, channel 1",
      "desc": "The TCA9555 on a breakout.",
      "test": "Not built: checked against Rev A's netlist.",
      "color": "#c8202f"
    }
  ],
  "ics": [
    {
      "id": "U402",
      "value": "DG412",
      "label": "DG412",
      "stage": 1,
      "pins": [
        {
          "n": 1,
          "r": 2,
          "c": "e",
          "net": "SW_EN1"
        },
        {
          "n": 2,
          "r": 3,
          "c": "e",
          "net": "to jack"
        },
        {
          "n": 3,
          "r": 4,
          "c": "e",
          "net": "CVDRV1"
        },
        {
          "n": 4,
          "r": 5,
          "c": "e"
        },
        {
          "n": 5,
          "r": 6,
          "c": "e"
        },
        {
          "n": 6,
          "r": 7,
          "c": "e"
        },
        {
          "n": 7,
          "r": 8,
          "c": "e"
        },
        {
          "n": 8,
          "r": 9,
          "c": "e"
        },
        {
          "n": 9,
          "r": 9,
          "c": "f"
        },
        {
          "n": 10,
          "r": 8,
          "c": "f"
        },
        {
          "n": 11,
          "r": 7,
          "c": "f"
        },
        {
          "n": 12,
          "r": 6,
          "c": "f"
        },
        {
          "n": 13,
          "r": 5,
          "c": "f"
        },
        {
          "n": 14,
          "r": 4,
          "c": "f"
        },
        {
          "n": 15,
          "r": 3,
          "c": "f"
        },
        {
          "n": 16,
          "r": 2,
          "c": "f"
        }
      ]
    },
    {
      "id": "U701",
      "value": "TCA9555",
      "label": "TCA9555",
      "stage": 1,
      "pins": [
        {
          "n": 1,
          "r": 12,
          "c": "e"
        },
        {
          "n": 2,
          "r": 13,
          "c": "e"
        },
        {
          "n": 3,
          "r": 14,
          "c": "e"
        },
        {
          "n": 4,
          "r": 15,
          "c": "e",
          "net": "SW_EN1"
        },
        {
          "n": 5,
          "r": 16,
          "c": "e"
        },
        {
          "n": 6,
          "r": 17,
          "c": "e"
        },
        {
          "n": 7,
          "r": 18,
          "c": "e"
        },
        {
          "n": 8,
          "r": 19,
          "c": "e"
        },
        {
          "n": 9,
          "r": 20,
          "c": "e"
        },
        {
          "n": 10,
          "r": 21,
          "c": "e"
        },
        {
          "n": 11,
          "r": 22,
          "c": "e"
        },
        {
          "n": 12,
          "r": 23,
          "c": "e"
        },
        {
          "n": 13,
          "r": 23,
          "c": "f"
        },
        {
          "n": 14,
          "r": 22,
          "c": "f"
        },
        {
          "n": 15,
          "r": 21,
          "c": "f"
        },
        {
          "n": 16,
          "r": 20,
          "c": "f"
        },
        {
          "n": 17,
          "r": 19,
          "c": "f"
        },
        {
          "n": 18,
          "r": 18,
          "c": "f"
        },
        {
          "n": 19,
          "r": 17,
          "c": "f"
        },
        {
          "n": 20,
          "r": 16,
          "c": "f"
        },
        {
          "n": 21,
          "r": 15,
          "c": "f"
        },
        {
          "n": 22,
          "r": 14,
          "c": "f"
        },
        {
          "n": 23,
          "r": 13,
          "c": "f"
        },
        {
          "n": 24,
          "r": 12,
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
          "r": 25,
          "c": "e",
          "net": "CVDRV1"
        },
        {
          "n": 2,
          "r": 26,
          "c": "e"
        },
        {
          "n": 3,
          "r": 27,
          "c": "e"
        },
        {
          "n": 4,
          "r": 28,
          "c": "e"
        },
        {
          "n": 5,
          "r": 29,
          "c": "e"
        },
        {
          "n": 6,
          "r": 30,
          "c": "e"
        },
        {
          "n": 7,
          "r": 31,
          "c": "e"
        },
        {
          "n": 8,
          "r": 31,
          "c": "f"
        },
        {
          "n": 9,
          "r": 30,
          "c": "f"
        },
        {
          "n": 10,
          "r": 29,
          "c": "f"
        },
        {
          "n": 11,
          "r": 28,
          "c": "f"
        },
        {
          "n": 12,
          "r": 27,
          "c": "f"
        },
        {
          "n": 13,
          "r": 26,
          "c": "f"
        },
        {
          "n": 14,
          "r": 25,
          "c": "f"
        }
      ]
    }
  ],
  "twoPins": [
    {
      "id": "R407",
      "type": "R",
      "value": "4.7k",
      "r1": 2,
      "c1": "b",
      "r2": 3,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "R406",
      "type": "R",
      "value": "1k",
      "r1": 3,
      "c1": "c",
      "r2": 10,
      "c2": "c",
      "stage": 1
    },
    {
      "id": "D401",
      "type": "D",
      "value": "TVS",
      "r1": 10,
      "c1": "b",
      "r2": 11,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "R404",
      "type": "R",
      "value": "1k",
      "r1": 10,
      "c1": "d",
      "r2": 11,
      "c2": "d",
      "stage": 1
    }
  ],
  "jumpers": [
    {
      "id": "W1",
      "r1": 2,
      "c1": "a",
      "r2": 15,
      "c2": "a",
      "label": "SW_EN1",
      "stage": 1
    },
    {
      "id": "W2",
      "r1": 9,
      "c1": "ctrlLi",
      "r2": 10,
      "c2": "a",
      "label": "CV 1",
      "stage": 1
    },
    {
      "id": "W3",
      "r1": 4,
      "c1": "a",
      "r2": 25,
      "c2": "a",
      "label": "CVDRV1",
      "stage": 1
    }
  ],
  "powerWires": [],
  "jpsWires": [
    {
      "id": "J410.1",
      "ref": "J410",
      "pad": "1",
      "label": "CV 1",
      "lbl": "CV 1",
      "row": 9,
      "col": "ctrlLo",
      "stage": 1
    }
  ],
  "netLabels": [
    {
      "r": 11,
      "side": "L",
      "name": "to the ADC",
      "stage": 1
    }
  ],
  "boySteps": [
    {
      "net": "CVDRV1",
      "line": "CVDRV1       U502.1 (DAC stage), U402.3",
      "rows": [
        "25L",
        "4L"
      ],
      "ctrl": [],
      "parts": [
        "U402",
        "U502"
      ],
      "wires": [
        "W3"
      ],
      "holes": [
        [
          4,
          "e"
        ],
        [
          25,
          "e"
        ]
      ]
    },
    {
      "net": "SW_EN1",
      "line": "SW_EN1       U701.4 P00 (expander), R407 4.7k, U402.1",
      "rows": [
        "15L",
        "2L"
      ],
      "ctrl": [],
      "parts": [
        "R407",
        "U402",
        "U701"
      ],
      "wires": [
        "W1"
      ],
      "holes": [
        [
          2,
          "b"
        ],
        [
          2,
          "e"
        ],
        [
          15,
          "e"
        ]
      ]
    },
    {
      "net": "Net-(R406-Pad1)",
      "line": "switch out   U402.2, R406",
      "rows": [
        "3L"
      ],
      "ctrl": [],
      "parts": [
        "R406",
        "U402"
      ],
      "wires": [],
      "holes": [
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
      "net": "CV1",
      "line": "CV1          R406 1k, J410 (jack), D401 TVS, R404 \u2192 ADC",
      "rows": [
        "10L"
      ],
      "ctrl": [
        "9L"
      ],
      "parts": [
        "D401",
        "J410",
        "R404",
        "R406"
      ],
      "wires": [
        "W2"
      ],
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
          9,
          "ctrlLo"
        ]
      ]
    }
  ]
});
