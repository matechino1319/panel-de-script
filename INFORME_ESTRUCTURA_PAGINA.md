# Informe de estructura del panel

## 1. Objetivo general

El proyecto `PanelScriptsHTML` es una pagina web simple para seleccionar scripts, subir un archivo y descargar el resultado generado.

La idea principal es:

- una pagina principal de entrada
- una pagina de scripts
- un backend en Python que ejecuta los scripts
- descarga directa del archivo generado

No tiene login, usuarios ni base de datos.

## 2. Estructura de archivos

Los archivos principales del panel son:

- [index.html](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/index.html): pagina principal
- [scripts.html](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/scripts.html): pagina donde se muestran y ejecutan los scripts
- [style.css](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/style.css): estilos visuales
- [script.js](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/script.js): logica del frontend
- [app.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/app.py): backend Flask
- [start.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/start.py): arranque auxiliar
- [abrir_panel.bat](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/abrir_panel.bat): lanzador rapido
- [script_runtime.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/script_runtime.py): ayuda comun para scripts

Scripts disponibles dentro del mismo panel:

- [1 Informe Biometrico.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/1%20Informe%20Biometrico.py)
- [2 Convenios.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/2%20Convenios.py)
- [3 Empleados.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/3%20Empleados.py)
- [4 Jubilados.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/4%20Jubilados.py)
- [5 Vecinos.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/5%20Vecinos.py)
- [6 Procesar excel transferencias.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/6%20Procesar%20excel%20transferencias.py)
- [convenios.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/convenios.py)

## 3. Estructura visual

### 3.1 Pagina principal

La principal esta pensada como portada.

Tiene:

- encabezado con nombre del sistema
- navegacion simple
- bloque principal con titulo
- un solo boton de acceso al panel
- tarjeta lateral de resumen
- pie de pagina

Su funcion es presentar el sistema y mandar a la pagina operativa.

### 3.2 Pagina de scripts

La pagina `scripts.html` es la parte de uso real.

Tiene:

- encabezado
- titulo principal `Scripts`
- texto corto de uso
- indicador de estado del servidor
- buscador de scripts
- boton para volver al inicio
- grilla de tarjetas de scripts
- panel de actividad

Cada tarjeta de script tiene:

- nombre
- descripcion
- selector de archivo
- boton ejecutar

## 4. Logica del frontend

La logica del frontend esta en [script.js](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/script.js).

Hace estas tareas:

- consulta al backend la lista de scripts con `/api/scripts`
- dibuja automaticamente las tarjetas
- asigna el filtro de extensiones permitido a cada input
- permite seleccionar archivo
- habilita el boton ejecutar cuando hay archivo
- arma un `FormData` con:
  - `script_id`
  - `file`
- envia la peticion a `/api/run`
- recibe el archivo generado
- dispara la descarga en el navegador
- muestra mensajes en el panel de actividad

Ademas:

- permite filtrar por texto con el buscador
- permite limpiar la consola visual
- muestra el estado del backend

## 5. Logica del backend

La logica del backend esta en [app.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/app.py).

### 5.1 Framework

Usa Flask.

### 5.2 Responsabilidades del backend

El backend se encarga de:

- servir `index.html`, `scripts.html`, `style.css` y `script.js`
- publicar el catalogo de scripts
- recibir el archivo subido
- validar tipo de archivo
- ejecutar el script seleccionado
- detectar el archivo de salida generado
- devolver la salida como descarga

### 5.3 Catalogo de scripts

Dentro de `app.py` existe `SCRIPT_CATALOG`.

Cada entrada define:

- `id`
- `title`
- `script`
- `description`
- `accept`

`accept` controla el filtro del selector de archivos en la interfaz.

### 5.4 Endpoints

Los endpoints principales son:

- `/` -> pagina principal
- `/scripts.html` -> pagina de scripts
- `/api/scripts` -> devuelve el catalogo
- `/api/run` -> ejecuta el script con el archivo subido

### 5.5 Flujo de ejecucion

Cuando el usuario ejecuta un script:

1. el frontend sube el archivo
2. el backend crea una carpeta temporal
3. guarda el archivo subido ahi
4. define variables de entorno para el script
5. ejecuta el script con Python
6. busca el archivo de salida generado
7. lo carga en memoria
8. lo devuelve como descarga
9. elimina la carpeta temporal

## 6. Logica de aislamiento

El panel no deberia trabajar sobre carpetas fijas del usuario para cada corrida.

La corrida usa:

- una carpeta temporal para entrada
- una carpeta temporal para salida
- variables de entorno para decirle al script donde esta el archivo

Eso reduce errores por:

- mezclar archivos viejos
- tomar un archivo que no corresponde
- dejar salidas permanentes del panel dentro del proyecto

## 7. Rol de script_runtime.py

[script_runtime.py](/C:/Users/Mateo%20Martinez/Documents/New%20project/PanelScriptsHTML/script_runtime.py) da funciones de apoyo para los scripts.

Principalmente:

- `get_input_dir()`
- `get_output_dir()`
- `get_input_file()`
- `find_files()`

Sirve para que los scripts puedan adaptarse mejor al archivo subido desde la web sin depender tanto de una carpeta fija.

## 8. Comportamiento de descarga

El panel no fija una carpeta exacta de descarga.

Lo que hace es:

- forzar la descarga del archivo en el navegador
- dejar que Chrome o Edge decidan si:
  - guardan directo
  - o preguntan donde guardar

Si el navegador tiene activada la opcion de preguntar, el usuario puede elegir la carpeta manualmente.

## 9. Alcance de la pagina

La pagina esta pensada como una interfaz de uso simple.

No hace:

- autenticacion
- multiusuario
- historial persistente de corridas
- almacenamiento definitivo de resultados
- administracion avanzada

Si en el futuro creciera, se podria separar mejor en:

- frontend
- backend
- capa de configuracion de scripts
- bitacora de ejecuciones

## 10. Estado actual del diseño

Visualmente la pagina hoy esta organizada en dos vistas:

- principal
- scripts

La principal ya quedo reducida a una entrada simple, con menos relleno visual.

La pagina de scripts mantiene:

- titulo corto
- buscador
- tarjetas
- actividad

## 11. Recomendacion de trabajo a futuro

La linea mas ordenada para seguir es esta:

1. no tocar la logica interna de tablas salvo cuando falle un caso real
2. usar la pagina solo como interfaz de seleccion y ejecucion
3. mantener cada script con su estructura esperada
4. mejorar solo:
   - interfaz
   - nombres de salida
   - mensajes de error
   - compatibilidad de entrada cuando haga falta

## 12. Resumen final

Hoy el sistema funciona con esta idea:

- una home simple
- una pagina de scripts
- backend Flask
- ejecucion controlada de scripts
- descarga directa del resultado

La pagina no busca reemplazar la logica de los scripts.
Su rol es ordenar el acceso, la carga de archivos y la descarga del resultado.
