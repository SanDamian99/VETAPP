Aplicación con Streamlit y Google Generative AI

Esta es una aplicación basada en Streamlit que utiliza Google Generative AI para generar contenido, manejar excepciones de red y mostrar una interfaz web interactiva.

Requisitos

Antes de ejecutar la aplicación, asegúrese de tener instaladas las dependencias necesarias. Estas se encuentran en el archivo requirements.txt.

Instalación de dependencias

Ejecute el siguiente comando para instalar todas las librerías necesarias:

pip install -r requirements.txt

Uso

Para ejecutar la aplicación, simplemente ejecute el siguiente comando en la terminal:

streamlit run app.py

Donde app.py es el archivo principal de la aplicación.

Dependencias principales

Streamlit: Para la interfaz web interactiva.

Google Generative AI: Para la generación de contenido con modelos de Google.

Requests y urllib3: Para manejar solicitudes HTTP y sus excepciones.

Google API Core: Para manejar errores relacionados con las APIs de Google.

Manejo de errores

La aplicación maneja las siguientes excepciones:

ConnectionError: Para problemas de conexión de red.

ProtocolError: Para errores de comunicación HTTP.

TooManyRequests: Para el manejo de límites de peticiones en la API de Google.
