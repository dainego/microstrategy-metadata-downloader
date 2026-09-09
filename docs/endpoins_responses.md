# Tipos de Objeto
## OBJECT_TYPE_ATTRIBUTE = 12
Endpoint: /api/model/attributes/{attribute_id}
Ejemplo:
{
  "information": {
    "dateCreated": "2018-08-07T17:18:28.000Z",
    "dateModified": "2026-07-31T01:36:02.813Z",
    "versionId": "63DD674B1040E1E67B4981808C435B3F",
    "acg": 255,
    "primaryLocale": "en-US",
    "objectId": "2FE256AB41C033EFDD200E8262214EFE",
    "subType": "attribute",
    "name": "Tipo de Suscripcion",
    "description": "Clasificacion definida en T3 para la suscripcion"
  },
  "forms": [
    {
      "id": "45C11FA478E745FEA08D781CEA190FE5",
      "name": "ID",
      "category": "ID",
      "type": "system",
      "displayFormat": "number",
      "dataType": {
        "type": "integer",
        "precision": 2,
        "scale": -2147483648
      },
      "expressions": [
        {
          "expressionId": "90A9F24649CD41DDAAC20C88EBBEAA28",
          "expression": {
            "text": "Tipo_Suscripcion_ID"
          },
          "tables": [
            {
              "objectId": "33F916C44C7D144C5FF67EA20CB187B8",
              "subType": "logical_table",
              "name": "D_TIPO_SUSCRIPCION"
            },
            {
              "objectId": "A84013DF4C78104501E7B3BC6E1421C1",
              "subType": "logical_table",
              "name": "F_PS_SUSCRIPCION_D_VW"
            }
          ]
        }
      ],
      "alias": "Tipo_Suscripcion_ID",
      "lookupTable": {
        "objectId": "33F916C44C7D144C5FF67EA20CB187B8",
        "subType": "logical_table",
        "name": "D_TIPO_SUSCRIPCION"
      }
    },
    {
      "id": "CCFBE2A5EADB4F50941FB879CCF1721C",
      "name": "DESC",
      "category": "DESC",
      "type": "system",
      "displayFormat": "text",
      "dataType": {
        "type": "n_var_char",
        "precision": 50,
        "scale": -2147483648
      },
      "expressions": [
        {
          "expressionId": "98A22937243946ACB5169E7873B4FF89",
          "expression": {
            "text": "Tipo_Suscripcion_DE"
          },
          "tables": [
            {
              "objectId": "33F916C44C7D144C5FF67EA20CB187B8",
              "subType": "logical_table",
              "name": "D_TIPO_SUSCRIPCION"
            }
          ]
        }
      ],
      "alias": "Tipo_Suscripcion_DE",
      "lookupTable": {
        "objectId": "33F916C44C7D144C5FF67EA20CB187B8",
        "subType": "logical_table",
        "name": "D_TIPO_SUSCRIPCION"
      }
    }
  ],
  "attributeLookupTable": {
    "objectId": "33F916C44C7D144C5FF67EA20CB187B8",
    "subType": "logical_table",
    "name": "D_TIPO_SUSCRIPCION"
  },
  "keyForm": {
    "id": "45C11FA478E745FEA08D781CEA190FE5",
    "name": "ID"
  },
  "displays": {
    "reportDisplays": [
      {
        "id": "CCFBE2A5EADB4F50941FB879CCF1721C",
        "name": "DESC"
      }
    ],
    "browseDisplays": [
      {
        "id": "CCFBE2A5EADB4F50941FB879CCF1721C",
        "name": "DESC"
      }
    ]
  },
  "sorts": {},
  "relationships": [
    {
      "parent": {
        "objectId": "2FE256AB41C033EFDD200E8262214EFE",
        "subType": "attribute",
        "name": "Tipo de Suscripcion"
      },
      "child": {
        "objectId": "764FA25244C7BFD2F8D9F9B9B2E27CB8",
        "subType": "attribute",
        "name": "Suscripcion Historico ID"
      },
      "relationshipTable": {
        "objectId": "A84013DF4C78104501E7B3BC6E1421C1",
        "subType": "logical_table",
        "name": "F_PS_SUSCRIPCION_D_VW"
      },
      "relationshipType": "one_to_many"
    },
    {
      "parent": {
        "objectId": "2FE256AB41C033EFDD200E8262214EFE",
        "subType": "attribute",
        "name": "Tipo de Suscripcion"
      },
      "child": {
        "objectId": "580D52CC4D55EE96F7726B8B894EA7A4",
        "subType": "attribute",
        "name": "Tipo Suscripcion ID"
      },
      "relationshipTable": {
        "objectId": "33F916C44C7D144C5FF67EA20CB187B8",
        "subType": "logical_table",
        "name": "D_TIPO_SUSCRIPCION"
      },
      "relationshipType": "one_to_many"
    }
  ],
  "nonAggregatable": false,
  "applySecurityFiltersToElementBrowsing": false,
  "enableElementCaching": true,
  "elementDisplayOption": "limited_elements",
  "elementDisplayLimit": 100
}
Atributos a devolver: 
* information:
    objectId
    name
    subtype
    description (clean_text)
* expressions:
    text
    tables:
        objectId
        subType
        name

## OBJECT_TYPE_METRIC = 4
Endpoint: /api/model/metrics/{metric_id}
Ejemplo:
{
  "information": {
    "dateCreated": "2018-08-08T19:38:56.000Z",
    "dateModified": "2020-06-26T16:51:54.685Z",
    "versionId": "572B579711EAB7CD00000080EF452733",
    "acg": 255,
    "primaryLocale": "en-US",
    "objectId": "018F254040F401995CCA988822D55C98",
    "subType": "metric",
    "name": "Suscripciones",
    "description": "Cuantificacion de suscripciones (Activas, Canceladas, Suspendidas)"
  },
  "expression": {
    "text": "Sum({Suscripciones CA})"
  },
  "dimty": {
    "dimtyUnits": [
      {
        "dimtyUnitType": "report_base_level",
        "aggregation": "normal",
        "filtering": "apply",
        "groupBy": true
      },
      {
        "dimtyUnitType": "attribute",
        "target": {
          "objectId": "9360EB0641A3E19F4578C1B528939477",
          "subType": "attribute",
          "name": "Fecha"
        },
        "aggregation": "last_in_relationship",
        "filtering": "apply",
        "groupBy": true
      }
    ],
    "excludeAttribute": false,
    "allowAddingUnit": true
  },
  "conditionality": {
    "filter": {
      "objectId": "E06E42694F4A3AADE28333A3999A5183",
      "subType": "filter",
      "name": "Max Fecha Suscripcion"
    },
    "embedMethod": "metric_into_report_filter",
    "removeElements": false
  },
  "metricSubtotals": [
    {
      "definition": {
        "objectId": "96C487AF4D12472A910C1ACACFB56EFB",
        "subType": "system_subtotal",
        "name": "Total"
      }
    },
    {
      "definition": {
        "objectId": "078C50834B484EE29948FA9DD5300ADF",
        "subType": "system_subtotal",
        "name": "Count"
      }
    },
    {
      "definition": {
        "objectId": "B328C60462634223B2387D4ADABEEB53",
        "subType": "system_subtotal",
        "name": "Average"
      }
    },
    {
      "definition": {
        "objectId": "00B7BFFF967F42C4B71A4B53D90FB095",
        "subType": "system_subtotal",
        "name": "Minimum"
      }
    },
    {
      "definition": {
        "objectId": "B1F4AA7DE683441BA559AA6453C5113E",
        "subType": "system_subtotal",
        "name": "Maximum"
      }
    },
    {
      "definition": {
        "objectId": "54E7BFD129514717A92BC44CF1FE5A32",
        "subType": "system_subtotal",
        "name": "Product"
      }
    },
    {
      "definition": {
        "objectId": "83A663067F7E43B2ABF67FD38ECDC7FE",
        "subType": "system_subtotal",
        "name": "Median"
      }
    },
    {
      "definition": {
        "objectId": "36226A4048A546139BE0AF5F24737BA8",
        "subType": "system_subtotal",
        "name": "Mode"
      }
    },
    {
      "definition": {
        "objectId": "7FBA414995194BBAB2CF1BB599209824",
        "subType": "system_subtotal",
        "name": "Standard Deviation"
      }
    },
    {
      "definition": {
        "objectId": "1769DBFCCF2D4392938E40418C6E065E",
        "subType": "system_subtotal",
        "name": "Variance"
      }
    },
    {
      "definition": {
        "objectId": "E1853D5A36C74F59A9F8DEFB3F9527A1",
        "subType": "system_subtotal",
        "name": "Geometric Mean"
      }
    },
    {
      "definition": {
        "objectId": "F225147A4CA0BB97368A5689D9675E73",
        "subType": "system_subtotal",
        "name": "Aggregation"
      },
      "implementation": {
        "objectId": "96C487AF4D12472A910C1ACACFB56EFB",
        "subType": "system_subtotal",
        "name": "Total"
      }
    }
  ],
  "aggregateFromBase": false,
  "formulaJoinType": "default",
  "smartTotal": "decomposable_false",
  "dataType": {
    "type": "reserved",
    "precision": 0,
    "scale": 0
  },
  "format": {
    "header": [],
    "values": [
      {
        "type": "number_category",
        "value": "0"
      },
      {
        "type": "number_decimal_places",
        "value": "0"
      },
      {
        "type": "number_format",
        "value": "#,##0;(#,##0)"
      }
    ]
  },
  "subtotalFromBase": false,
  "metricFormatType": "reserved",
  "thresholds": []
}
Atributos a devolver: Un registro por cada ocurrencia de information, expression y conditionality.
* information:
    objectId
    name
    subtype
    description (clean_text)
* expression:
    text
* conditionality:
    filter:
        objectId
        subType
        name 
## OBJECT_TYPE_FILTER = 1
Endpoint: /api/model/filters/{filter_id}
Ejemplo:
{
  "information": {
    "dateCreated": "2018-12-03T18:32:12.576Z",
    "dateModified": "2025-01-06T12:40:16.715Z",
    "versionId": "FCD1E407B946A0C4698EC4BF92F75971",
    "acg": 255,
    "primaryLocale": "en-US",
    "objectId": "4B36BB5F4843105F55C1DA85675D9165",
    "subType": "filter",
    "name": "Tipo de Comprobante - Recarga",
    "description": "Tipo de comprobante In List(RCG:Recarga Subscripcion)"
  },
  "qualification": {
    "text": "{Tipo de Comprobante} = RCG:Recarga Subscripción",
    "tree": {
      "type": "predicate_element_list",
      "predicateId": "A489BA80A6884ECC9CCA3EAC857929A5",
      "predicateTree": {
        "attribute": {
          "objectId": "E8AF924D4D5495E51828528A19051291",
          "subType": "attribute",
          "name": "Tipo de Comprobante"
        },
        "elements": [
          {
            "display": "RCG:Recarga Subscripción",
            "elementId": "h5"
          }
        ],
        "function": "in"
      }
    }
  }
}
Atributos a devolver: Un registro por cada ocurrencia del information, qualification, tree, predicateTree y elements
* information:
    objectId
    name
    subtype
    description (clean_text)
* qualification:
    text
        tree:
            type
                predicateTree:
                    objectId
                    subType
                    name
                    function
                    elements:
                        display
                        elementId

## OBJECT_TYPE_FACT = 13
Endpoint: /api/model/facts/{fact_id}
Ejemplo:
{
  "information": {
    "dateCreated": "2018-07-20T13:19:39.000Z",
    "dateModified": "2020-07-21T21:12:14.680Z",
    "versionId": "55F5CDC011EAB64200000080EF75DF54",
    "acg": 255,
    "primaryLocale": "en-US",
    "objectId": "44F9C14B4192D668C33510AAC2BE1251",
    "subType": "fact",
    "name": "Suscripciones CA"
  },
  "dataType": {
    "type": "integer",
    "precision": 2,
    "scale": 0
  },
  "expressions": [
    {
      "expressionId": "02C7C2F55A93438A8BCDAD0B8B44E7AF",
      "expression": {
        "text": "Suscripcion_CA"
      },
      "tables": [
        {
          "objectId": "C74E6E424E7DD03B60F160A74C45C16A",
          "subType": "logical_table",
          "name": "F_AG_Suscripcion_01_D_VW"
        },
        {
          "objectId": "512AD76240D6E90B96E549880581F6F4",
          "subType": "logical_table",
          "name": "F_AG_Suscripcion_02_D_VW"
        },
        {
          "objectId": "A84013DF4C78104501E7B3BC6E1421C1",
          "subType": "logical_table",
          "name": "F_PS_SUSCRIPCION_D_VW"
        },
        {
          "objectId": "DE60EF3544618CA627540C878DFD4C0D",
          "subType": "logical_table",
          "name": "F_AG_Suscripcion_03_D_VW"
        }
      ]
    },
    {
      "expressionId": "D0A785B966B94F5CAC6A04C675D4DF44",
      "expression": {
        "text": "Suscripcion_CA"
      },
      "tables": [
        {
          "objectId": "01B67D04409837ECEE77618A6C21266D",
          "subType": "logical_table",
          "name": "F_AG_Suscripcion_04_D_VW"
        },
        {
          "objectId": "F54F0169480496ACD9ED15B0F1620DD2",
          "subType": "logical_table",
          "name": "F_AG_Suscripcion_05_D_VW"
        }
      ]
    }
  ],
  "extensions": [],
  "entryLevel": [
    {
      "objectId": "9360EB0641A3E19F4578C1B528939477",
      "subType": "attribute",
      "name": "Fecha"
    },
    {
      "objectId": "1F1FF9E245C2D8D7F08E6F959ED1288E",
      "subType": "attribute",
      "name": "Flag Bono Activo Tenencia Familia"
    },
    {
      "objectId": "5A8DC0F94FBAFF1D72865B98BDABC384",
      "subType": "attribute",
      "name": "Parque Tecnico ID"
    },
    {
      "objectId": "EABCB0684291600237E1B3A1E3D7F742",
      "subType": "attribute",
      "name": "Segmento Tenencia Movistar Con Todo"
    },
    {
      "objectId": "764FA25244C7BFD2F8D9F9B9B2E27CB8",
      "subType": "attribute",
      "name": "Suscripcion Historico ID"
    }
  ],
  "alias": "Suscripciones_CA"
}
Atributos a devolver: un regitro por cada ocurrencia de information, expression y table
* information:
    objectId
    name
    subtype
    description (clean_text)
* expressions:
   text
   tables:
    name