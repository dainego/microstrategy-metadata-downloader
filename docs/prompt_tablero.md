# Nuevo Tablero Metadata Microstrategy:
Tablero para navegar la metadata de la herramienta Microstrategy.

## Objetos soportados
* Attributos
* Métricas
    * Facts
    * Filtros de métricas 

## Diseño

### En la parte superior se debe mostrar una sección con los siguiente KPIs:
* Cantidad total de Modelos
* Cantidad total de Submodelos

### En la parte ionferior los detalles

#### Relaciones:
##### Primer nivel 
folder, model, submodel, submodel1, submodel2, submodel3. -> Todos los archivos
##### Segundo nivel
tableName -> facts y attributes
##### Tercer nivel
metrics (se relacionan con facts a través del campo expression)
##### Cuarto nivel
filters  (se realcionan con metrics a través del campo filterObjectId, y con attributes a través del campo predicateObjectId)


## Modelos Lógicos
Aagregar una sección  de modelos lógicos donde por cada tabla fact (F_) se vea gráficamente el modelo logico, el cual contiene en el centro la fact (F_) con todos sus hechos y métricas y alrededor los atributos con mencion de la tabla  (D_) a la que refiere cada uno.