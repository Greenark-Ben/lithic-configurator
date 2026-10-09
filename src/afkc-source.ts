export const AFKC_SOURCE = {
  "schema": "LITHIC.manufacturer-window-prototype.v0.1",
  "product": {
    "manufacturer": "Elitfonster",
    "range": "Original Alu 100",
    "productCode": "AFKC",
    "productId": "ELITFONSTER-AFKC-PROTOTYPE-001",
    "description": "Source-based fixed-window prototype derived from drawing 61-37-F221 rev A",
    "evidenceStatus": "UNAPPROVED_MANUFACTURER_SOURCE_PROTOTYPE",
    "definitionVersion": "0.1",
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
      "value": 2,
      "status": "PROTOTYPE_SIMPLIFICATION"
    }
  },
  "orientation": {
    "hostNormalPositive": "exterior",
    "hostNormalNegative": "interior",
    "aluminiumSide": "exterior",
    "profileDepthOrigin": "timber section centre; negative depth values are interior"
  },
  "profiles": {
    "timberHead": {
      "section": "A",
      "pointsMm": [
        [
          0,
          -52.5
        ],
        [
          53.5,
          -52.5
        ],
        [
          53.5,
          -37.5
        ],
        [
          40.5,
          -37.5
        ],
        [
          40.5,
          10.5
        ],
        [
          53.5,
          10.5
        ],
        [
          53.5,
          52.5
        ],
        [
          0,
          52.5
        ]
      ]
    },
    "timberSill": {
      "section": "B",
      "pointsMm": [
        [
          0,
          -52.5
        ],
        [
          36,
          -52.5
        ],
        [
          40.5,
          -37.5
        ],
        [
          40.5,
          10.5
        ],
        [
          53.5,
          10.5
        ],
        [
          53.5,
          52.5
        ],
        [
          0,
          52.5
        ]
      ]
    },
    "timberJamb": {
      "section": "C/D",
      "pointsMm": [
        [
          0,
          -52.5
        ],
        [
          53.5,
          -52.5
        ],
        [
          53.5,
          -37.5
        ],
        [
          40.5,
          -37.5
        ],
        [
          40.5,
          10.5
        ],
        [
          53.5,
          10.5
        ],
        [
          53.5,
          52.5
        ],
        [
          0,
          52.5
        ]
      ]
    },
    "aluminiumHeadJamb": {
      "section": "A/C/D",
      "pointsMm": [
        [
          0,
          -62.5
        ],
        [
          53.5,
          -62.5
        ],
        [
          53.5,
          -60.5
        ],
        [
          2,
          -60.5
        ],
        [
          2,
          -52.5
        ],
        [
          0,
          -52.5
        ]
      ]
    },
    "aluminiumSill": {
      "section": "B",
      "pointsMm": [
        [
          0,
          -62.5
        ],
        [
          36,
          -62.5
        ],
        [
          41,
          -39
        ],
        [
          39,
          -38.5
        ],
        [
          34.5,
          -60.5
        ],
        [
          2,
          -60.5
        ],
        [
          2,
          -52.5
        ],
        [
          0,
          -52.5
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
    "AFKC Glazing Center Offset": "fixed formula derived from source section"
  },
  "junctionAssumption": "Full-height jamb sweeps; head and sill sweeps terminate at jamb inner faces. This is a prototype butt-joint rule, not a manufacturer fabrication claim.",
  "excludedSourceContent": [
    "Intermediate mullion and transom sections between A and B",
    "Optional internal slot detail",
    "Antique design option"
  ],
  "simplifications": [
    "Small seals and gasket bulbs are not separate solids",
    "Rounded timber edges and minor machining grooves are omitted",
    "Folded aluminium hooks are reduced to buildable polygonal profiles",
    "The 48 mm triple-glazing assembly is one material-controlled solid because pane and cavity dimensions are unresolved"
  ],
  "unresolved": [
    "Exact gasket geometries and materials",
    "Exact pane and cavity build-up within the 48 mm glazing assembly",
    "Manufacturer corner fabrication and drainage details",
    "Allowable manufactured size range"
  ]
} as const;

