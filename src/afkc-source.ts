export const AFKC_SOURCE = {
  "schema": "LITHIC.manufacturer-window-prototype.v0.1",
  "product": {
    "manufacturer": "Elitfonster",
    "range": "Original Alu 100",
    "productCode": "AFKC",
    "productId": "ELITFONSTER-AFKC-PROTOTYPE-001",
    "description": "AFKC source-derived prototype with reviewed native sweeps, separate panes, beads and seals",
    "evidenceStatus": "UNAPPROVED_MANUFACTURER_SOURCE_PROTOTYPE",
    "definitionVersion": "0.2",
    "approvedManufacturerContent": false
  },
  "sources": {
    "drawing": "61-37-F221",
    "revision": "A",
    "pdf": {
      "sha256": "3C3AED9AC9D11CB6842B7113F58CE728E4F97A16356C69AB073AD241A5965A8A",
      "filename": "Ritning-pdf---Elitfonster-Original-Alu-100-Fast-karm.pdf"
    },
    "dwg": {
      "sha256": "3AEF79EAFBED26EF81D73CE77A6FF7920D262609EED80B66BE51A5DA9B6787CD",
      "filename": "Ritning-dwg---Elitfonster-Original-Alu-100-Fast-karm.dwg"
    },
    "productPage": "https://www.elitfonster.se/vara-produkter/fonster/fast-karm/afkc/"
  },
  "configuration": {
    "widthMm": 1200,
    "heightMm": 1500,
    "dimensionMeaning": "Overall external timber-frame dimensions; synthetic test size only",
    "wallOpeningWidthMm": 1200,
    "wallOpeningHeightMm": 1500,
    "testSizeIsManufacturerAvailabilityClaim": false
  },
  "fixedSectionDimensions": {
    "timberDepthMm": {
      "value": 105,
      "status": "MEASURED_FROM_TRANSFORMED_DWG"
    },
    "frameSightlineMm": {
      "value": 53.5,
      "status": "DRAWING_DIMENSION_AND_DWG"
    },
    "glazingAssemblyDepthMm": {
      "value": 48,
      "status": "DRAWING_NOTE_AND_DWG"
    },
    "glazingCenterOffsetFromTimberCenterMm": {
      "value": -13.5,
      "positiveDirection": "exterior",
      "status": "DERIVED_FROM_DWG"
    },
    "glazingSeatOverlapMm": {
      "value": 13,
      "status": "DERIVED_FROM_DWG"
    },
    "aluminiumExteriorProjectionMm": {
      "value": 10,
      "status": "MEASURED_FROM_DWG"
    },
    "aluminiumNominalSkinMm": {
      "value": 1.3,
      "status": "VARIES_BY_SOURCE_FOLD_AND_REVIEWED_RETURN"
    }
  },
  "orientation": {
    "hostNormalPositive": "exterior",
    "hostNormalNegative": "interior",
    "aluminiumSide": "exterior",
    "profileDepthOrigin": "Source depth datum at timber centre; view/native exterior depth = negative source depth"
  },
  "profiles": {
    "timberHead": {
      "section": "A",
      "pointsMm": [
        [
          0,
          -50.5
        ],
        [
          2,
          -52.5
        ],
        [
          32.5,
          -52.5
        ],
        [
          34.5,
          -50.5
        ],
        [
          34.5,
          -40.3
        ],
        [
          31.5,
          -40.3
        ],
        [
          31.5,
          -37.3
        ],
        [
          34.5,
          -37.3
        ],
        [
          34.5,
          -8.65
        ],
        [
          31,
          -8.65
        ],
        [
          31,
          1.35
        ],
        [
          34.5,
          1.35
        ],
        [
          34.5,
          13.5
        ],
        [
          52.5,
          13.5
        ],
        [
          53.5,
          14.5
        ],
        [
          53.5,
          50.5
        ],
        [
          51.5,
          52.5
        ],
        [
          2,
          52.5
        ],
        [
          0,
          50.5
        ]
      ]
    },
    "timberJamb": {
      "section": "C/D",
      "pointsMm": [
        [
          0,
          -50.5
        ],
        [
          2,
          -52.5
        ],
        [
          32.5,
          -52.5
        ],
        [
          34.5,
          -50.5
        ],
        [
          34.5,
          -40.3
        ],
        [
          31.5,
          -40.3
        ],
        [
          31.5,
          -37.3
        ],
        [
          34.5,
          -37.3
        ],
        [
          34.5,
          -8.65
        ],
        [
          31,
          -8.65
        ],
        [
          31,
          1.35
        ],
        [
          34.5,
          1.35
        ],
        [
          34.5,
          13.5
        ],
        [
          52.5,
          13.5
        ],
        [
          53.5,
          14.5
        ],
        [
          53.5,
          50.5
        ],
        [
          51.5,
          52.5
        ],
        [
          2,
          52.5
        ],
        [
          0,
          50.5
        ]
      ]
    },
    "timberSill": {
      "section": "B",
      "pointsMm": [
        [
          0,
          -40.5
        ],
        [
          2,
          -42.5
        ],
        [
          15,
          -42.5
        ],
        [
          15.232181239,
          -50.290943073
        ],
        [
          17.221225029,
          -52.5
        ],
        [
          24.626768451,
          -52.5
        ],
        [
          26.611860754,
          -50.743738687
        ],
        [
          34.5,
          13.5
        ],
        [
          52.5,
          13.5
        ],
        [
          53.5,
          14.5
        ],
        [
          53.5,
          50.5
        ],
        [
          51.5,
          52.5
        ],
        [
          2,
          52.5
        ],
        [
          0,
          50.5
        ]
      ]
    },
    "beadHeadJamb": {
      "section": "A/C/D",
      "pointsMm": [
        [
          34.5,
          -39.2
        ],
        [
          40,
          -39.2
        ],
        [
          40,
          13.5
        ],
        [
          34.5,
          13.5
        ]
      ]
    },
    "beadSill": {
      "section": "B",
      "pointsMm": [
        [
          28.02925364,
          -39.2
        ],
        [
          39.545809647,
          -39.2
        ],
        [
          40.529621796,
          -38.2
        ],
        [
          40.529621796,
          12.566227087
        ],
        [
          39.545809647,
          13.5
        ],
        [
          38.029621796,
          13.5
        ],
        [
          38.029621796,
          10.5
        ],
        [
          34.131646317,
          10.5
        ]
      ]
    },
    "aluminiumHeadJamb": {
      "section": "A/C/D",
      "pointsMm": [
        [
          2.525,
          -62.5
        ],
        [
          38.57,
          -62.5
        ],
        [
          49.453,
          -41.211
        ],
        [
          49,
          -40.5
        ],
        [
          47,
          -40.5
        ],
        [
          46,
          -41.5
        ],
        [
          46,
          -44.2
        ],
        [
          43.363,
          -44.2
        ],
        [
          43,
          -41
        ],
        [
          41.15,
          -41
        ],
        [
          40.65,
          -42.366
        ],
        [
          41.423,
          -44.245
        ],
        [
          43.236,
          -45.4
        ],
        [
          45.336,
          -45.4
        ],
        [
          39.157,
          -60.334
        ],
        [
          37.798,
          -61.2
        ],
        [
          11.65,
          -61.2
        ],
        [
          10.65,
          -59.55
        ],
        [
          8.4,
          -57.3
        ],
        [
          3.1,
          -57.3
        ],
        [
          2.6,
          -54.2
        ],
        [
          3.8,
          -53.7
        ],
        [
          1.4,
          -53
        ],
        [
          1.4,
          -57.55
        ],
        [
          2.4,
          -58.55
        ],
        [
          8.4,
          -58.55
        ],
        [
          8.4,
          -61.25
        ],
        [
          2.525,
          -61.25
        ]
      ]
    },
    "aluminiumSill": {
      "section": "B plus reviewed prototype coverage return",
      "pointsMm": [
        [
          0,
          -62.5
        ],
        [
          38.55,
          -62.5
        ],
        [
          49.433,
          -41.211
        ],
        [
          48.98,
          -40.5
        ],
        [
          46.98,
          -40.5
        ],
        [
          45.98,
          -41.5
        ],
        [
          45.98,
          -44.2
        ],
        [
          43.343,
          -44.2
        ],
        [
          42.98,
          -41
        ],
        [
          41.13,
          -41
        ],
        [
          40.63,
          -42.366
        ],
        [
          41.403,
          -44.245
        ],
        [
          43.216,
          -45.4
        ],
        [
          45.316,
          -45.4
        ],
        [
          39.137,
          -60.334
        ],
        [
          37.778,
          -61.2
        ],
        [
          1.3,
          -61.2
        ],
        [
          1.3,
          -52.5
        ],
        [
          0,
          -52.5
        ]
      ]
    },
    "aluminiumCoverageReturn": {
      "section": "Reviewed prototype addition; not manufacturer-certified",
      "pointsMm": [
        [
          0,
          -62.5
        ],
        [
          3.1,
          -62.5
        ],
        [
          3.1,
          -61.25
        ],
        [
          1.3,
          -61.25
        ],
        [
          1.3,
          -52.5
        ],
        [
          0,
          -52.5
        ]
      ]
    },
    "glazingSeal": {
      "section": "Simplified visible seal finger",
      "pointsMm": [
        [
          47,
          -40.5
        ],
        [
          49,
          -40.5
        ],
        [
          52.4,
          -37.5
        ],
        [
          50.6,
          -37.5
        ]
      ]
    }
  },
  "nativeBindings": {
    "Width": "overall outer frame width",
    "Height": "overall outer frame height",
    "AFKC Timber Depth": "fixed formula from source section",
    "AFKC Frame Sightline": "fixed formula from source section",
    "AFKC Glazing Assembly Depth": "fixed formula from source section",
    "AFKC Glazing Center Offset": "fixed formula derived from source section",
    "timber": "Timber Material",
    "aluminium": "Aluminium Material",
    "glazing": "Glazing Material",
    "spacer": "Glazing Spacer Material",
    "seal": "Glazing Seal Material"
  },
  "junctionAssumption": "Native U-shaped head/jamb sweeps and distinct sill sweep with complementary 45 degree lower void cuts. Supplemental thin head/jamb return and extended sill return provide reviewed prototype coverage; not manufacturer corner fabrication.",
  "excludedSourceContent": [
    "Intermediate mullion and transom sections between A and B",
    "Optional internal slot detail",
    "Antique design option"
  ],
  "simplifications": [
    "Folded aluminium profiles use polygonal sections; source head/jamb and sill coordinates remain distinct",
    "A supplemental thin head/jamb return and extended sill return are reviewed prototype additions",
    "Three 4 mm panes with two 18 mm empty cavities; hollow aluminium spacers use a 7 mm radial section and 1 mm skin",
    "Visible glazing seal fingers are simplified; elastomer chemistry is unresolved",
    "Minor gasket bulbs, drainage and fastening details are omitted"
  ],
  "unresolved": [
    "Manufacturer corner fabrication, exact seal chemistry and drainage details",
    "Allowable manufactured size range",
    "Native parameter flex; exports remain fixed-size snapshots"
  ],
  "glazing": {
    "paneDepthRangesMm": [
      [
        -10.5,
        -6.5
      ],
      [
        11.5,
        15.5
      ],
      [
        33.5,
        37.5
      ]
    ],
    "cavityDepthRangesMm": [
      [
        -6.5,
        11.5
      ],
      [
        15.5,
        33.5
      ]
    ],
    "buildUpMm": [
      4,
      18,
      4,
      18,
      4
    ],
    "spacer": {
      "edgeInsetMm": 3.75,
      "radialHeightMm": 7,
      "skinMm": 1,
      "material": "aluminium",
      "status": "reviewed rectangular hollow simplification; not manufacturer-certified"
    }
  },
  "authoringRules": {
    "version": "afkc-native-authoring/0.2.2",
    "visualBaseline": {
      "widthMm": 1200,
      "heightMm": 1500,
      "reviewDate": "2026-10-13",
      "status": "USER_ACCEPTED_PROTOTYPE_VISUAL_BASELINE",
      "manufacturerApproved": false
    },
    "cladding": "native sweeps with native void cuts; preserve distinct main source sections",
    "timberAndBeads": "native polygon extrusions, separate beads",
    "seals": "native closed perimeter sweep",
    "forbiddenNativeTypes": [
      "FreeFormElement",
      "DirectShape"
    ],
    "plan": "coarse schematic, medium assembly, fine source profile symbols; hide model forms in plan",
    "parameterMode": "fixed-size-snapshot",
    "materialParameters": {
      "timber": "Timber Material",
      "aluminium": "Aluminium Material",
      "glazing": "Glazing Material",
      "spacer": "Glazing Spacer Material",
      "seal": "Glazing Seal Material"
    },
    "sharedParameterSchema": {
      "version": "lithic-revit-parameters/1",
      "parameters": [
        {
          "name": "Timber Material",
          "guid": "89233a69-2130-54f3-97c1-5099f3132b53",
          "dataType": "material",
          "binding": "type",
          "editable": true
        },
        {
          "name": "Aluminium Material",
          "guid": "8d688857-f368-50e3-8edb-c86fa80a8497",
          "dataType": "material",
          "binding": "type",
          "editable": true
        },
        {
          "name": "Glazing Material",
          "guid": "4f9948f6-c890-5b8e-b816-364776608ebb",
          "dataType": "material",
          "binding": "type",
          "editable": true
        },
        {
          "name": "Glazing Spacer Material",
          "guid": "6f44499d-0fc2-547f-85be-5ef9769c9f1e",
          "dataType": "material",
          "binding": "type",
          "editable": true
        },
        {
          "name": "Glazing Seal Material",
          "guid": "7e803715-2853-57eb-8061-f06126a367a3",
          "dataType": "material",
          "binding": "type",
          "editable": true
        },
        {
          "name": "LITHIC Request SHA256",
          "guid": "a08321d9-4db4-5642-88a3-2bb392356b84",
          "dataType": "text",
          "binding": "type",
          "editable": false
        },
        {
          "name": "LITHIC Source Drawing",
          "guid": "57488663-609d-5303-a491-9e67d3f9beaa",
          "dataType": "text",
          "binding": "type",
          "editable": false
        },
        {
          "name": "LITHIC Builder",
          "guid": "11f25f0f-1625-5cac-84b8-7cdc805d35a5",
          "dataType": "text",
          "binding": "type",
          "editable": false
        },
        {
          "name": "LITHIC Evidence Status",
          "guid": "bc500aa4-4004-533c-9969-b1baaa100fe2",
          "dataType": "text",
          "binding": "type",
          "editable": false
        },
        {
          "name": "LITHIC Geometry Mode",
          "guid": "f77a85c6-b9d5-5f72-9a02-aaa9a0200109",
          "dataType": "text",
          "binding": "type",
          "editable": false
        }
      ]
    }
  }
} as const;
