registerLayout("Boy: CV in, channel 1", {
  "title": "BOY: CV in, channel 1",
  "source": "tools/visualizer/boy_blocks.py; Rev A netlist",
  "board": "n8synth (single board, rows 1-36)",
  "boardId": "n8synth-10hp",
  "revision": "drawn, not built",
  "notes": "The ADS8688 on a breakout: 38 pins, for 8 channels.",
  "stages": [
    {
      "id": 1,
      "name": "CV in, channel 1",
      "desc": "The ADS8688 on a breakout: 38 pins, for 8 channels.",
      "test": "Not built: checked against Rev A's netlist.",
      "color": "#c8202f"
    }
  ],
  "ics": [
    {
      "id": "U401",
      "value": "ADS8688",
      "label": "ADS8688",
      "stage": 1,
      "pins": [
        {
          "n": 1,
          "r": 6,
          "c": "e"
        },
        {
          "n": 2,
          "r": 7,
          "c": "e"
        },
        {
          "n": 3,
          "r": 8,
          "c": "e"
        },
        {
          "n": 4,
          "r": 9,
          "c": "e"
        },
        {
          "n": 5,
          "r": 10,
          "c": "e"
        },
        {
          "n": 6,
          "r": 11,
          "c": "e"
        },
        {
          "n": 7,
          "r": 12,
          "c": "e"
        },
        {
          "n": 8,
          "r": 13,
          "c": "e"
        },
        {
          "n": 9,
          "r": 14,
          "c": "e"
        },
        {
          "n": 10,
          "r": 15,
          "c": "e"
        },
        {
          "n": 11,
          "r": 16,
          "c": "e"
        },
        {
          "n": 12,
          "r": 17,
          "c": "e"
        },
        {
          "n": 13,
          "r": 18,
          "c": "e"
        },
        {
          "n": 14,
          "r": 19,
          "c": "e"
        },
        {
          "n": 15,
          "r": 20,
          "c": "e"
        },
        {
          "n": 16,
          "r": 21,
          "c": "e",
          "net": "ADC_IN1"
        },
        {
          "n": 17,
          "r": 22,
          "c": "e"
        },
        {
          "n": 18,
          "r": 23,
          "c": "e"
        },
        {
          "n": 19,
          "r": 24,
          "c": "e"
        },
        {
          "n": 20,
          "r": 24,
          "c": "f"
        },
        {
          "n": 21,
          "r": 23,
          "c": "f"
        },
        {
          "n": 22,
          "r": 22,
          "c": "f"
        },
        {
          "n": 23,
          "r": 21,
          "c": "f"
        },
        {
          "n": 24,
          "r": 20,
          "c": "f"
        },
        {
          "n": 25,
          "r": 19,
          "c": "f"
        },
        {
          "n": 26,
          "r": 18,
          "c": "f"
        },
        {
          "n": 27,
          "r": 17,
          "c": "f"
        },
        {
          "n": 28,
          "r": 16,
          "c": "f"
        },
        {
          "n": 29,
          "r": 15,
          "c": "f"
        },
        {
          "n": 30,
          "r": 14,
          "c": "f"
        },
        {
          "n": 31,
          "r": 13,
          "c": "f"
        },
        {
          "n": 32,
          "r": 12,
          "c": "f"
        },
        {
          "n": 33,
          "r": 11,
          "c": "f"
        },
        {
          "n": 34,
          "r": 10,
          "c": "f"
        },
        {
          "n": 35,
          "r": 9,
          "c": "f"
        },
        {
          "n": 36,
          "r": 8,
          "c": "f"
        },
        {
          "n": 37,
          "r": 7,
          "c": "f"
        },
        {
          "n": 38,
          "r": 6,
          "c": "f"
        }
      ]
    }
  ],
  "twoPins": [
    {
      "id": "R405",
      "type": "R",
      "value": "100k",
      "r1": 21,
      "c1": "a",
      "r2": 21,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "C409",
      "type": "C",
      "value": "1n",
      "r1": 21,
      "c1": "b",
      "r2": 23,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "R404",
      "type": "R",
      "value": "1k",
      "r1": 28,
      "c1": "c",
      "r2": 21,
      "c2": "c",
      "stage": 1
    },
    {
      "id": "D401",
      "type": "D",
      "value": "TVS",
      "r1": 28,
      "c1": "b",
      "r2": 29,
      "c2": "pwrL",
      "stage": 1
    },
    {
      "id": "R406",
      "type": "R",
      "value": "1k",
      "r1": 33,
      "c1": "d",
      "r2": 28,
      "c2": "d",
      "stage": 1
    }
  ],
  "jumpers": [
    {
      "id": "W1",
      "r1": 25,
      "c1": "ctrlLi",
      "r2": 28,
      "c2": "a",
      "label": "CV 1",
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
      "row": 25,
      "col": "ctrlLo",
      "stage": 1
    }
  ],
  "netLabels": [
    {
      "r": 33,
      "side": "L",
      "name": "to the jack switch",
      "stage": 1
    }
  ],
  "boySteps": [
    {
      "net": "CV1",
      "line": "CV1          J410 (jack), D401 TVS, R404, R406 \u2192 switch",
      "rows": [
        "28L"
      ],
      "ctrl": [
        "25L"
      ],
      "parts": [
        "D401",
        "J410",
        "R404",
        "R406"
      ],
      "wires": [
        "W1"
      ],
      "holes": [
        [
          28,
          "c"
        ],
        [
          28,
          "b"
        ],
        [
          28,
          "d"
        ],
        [
          25,
          "ctrlLo"
        ]
      ]
    },
    {
      "net": "ADC_IN1",
      "line": "ADC_IN1      R404, R405 100k, C409 1n, U401.16 AIN_0P",
      "rows": [
        "21L"
      ],
      "ctrl": [],
      "parts": [
        "C409",
        "R404",
        "R405",
        "U401"
      ],
      "wires": [],
      "holes": [
        [
          21,
          "a"
        ],
        [
          21,
          "b"
        ],
        [
          21,
          "c"
        ],
        [
          21,
          "e"
        ]
      ]
    }
  ]
});
