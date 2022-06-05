# BVote

**Using blockchain to vote**

---
## Utilización del script autoBase.sh para inicializar las bases de datos

### Instalar Mariadb + crer usuario 'alumne' + crear base de datos usuarios.
```./autoBase.sh -i```

### Importar base de datos de las elecciones.
```./autoBase.sh -a <nombre elecciones> -R```

---
## Pasos a seguir para poner en marcha la web

### Ejecutar *login.js*.
```node login.js```

Antes de seguir adelante con las votaciones, los votantes deberán descargar sus claves y posteriormente se pondrán en funcionamiento los nodos corriendo la *blockchain*. De esta manera, las claves públicas de los votantes se guardarán en la base de datos y cuando ejecutemos los cuatro nodos estos podrán acceder a las claves. Por lo tanto, **después de que los votantes hayan descargado sus claves ejecutaremos**:

### Ejecutar el script **initBlockchain.sh** para inicializar la blockckain y comunicar los 4 nodos entre ellos.
```./initBlockchain.py <nombre elecciones> ```

---
Ahora sí, **los votantes podrán ejercer su voto a partir de aquí**.
Por último, siempre que se quieren ver los resultados de las elcciones asi como tambien las cadenas de bloques, se tendra que minar el bloque
```curl http://localhost:<puerto>/mine ```
