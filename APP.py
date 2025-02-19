import streamlit as st
import os
import re
import google.generativeai as genai
from requests.exceptions import ConnectionError
from urllib3.exceptions import ProtocolError
from google.api_core.exceptions import TooManyRequests

# =================== Configuración de la API de Gemini ===================

api_keys = [
"AIzaSyC5oc1_9Zp0xb37z2u7M1v3ov4Js1DyUSk",
"AIzaSyAEaxnxgoMXwg9YVRmRH_tKVGD3pNgHKkk"
]

current_api_key_index = 0

def configure_api():
    global current_api_key_index
    genai.configure(api_key=api_keys[current_api_key_index])

configure_api()

generation_config = {
    "temperature": 0.4,
    "top_p": 0.8,
    "top_k": 32,
    "max_output_tokens": 50,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

def create_model():
    return genai.GenerativeModel(model_name="gemini-2.0-flash",
                                 generation_config=generation_config,
                                 safety_settings=safety_settings)

model = create_model()

def switch_api_key():
    global current_api_key_index, model
    current_api_key_index = (current_api_key_index + 1) % len(api_keys)
    configure_api()
    model = create_model()

def send_prompt_to_gemini(prompt):
    try:
        response = model.generate_content([prompt])
        return response.text.strip() if response and response.text else "Sin respuesta."
    except Exception as e:
        switch_api_key()
        try:
            response = model.generate_content([prompt])
            return response.text.strip() if response and response.text else "Sin respuesta."
        except Exception as e:
            return "Error al procesar la solicitud."

# =================== Inicio de la aplicación Streamlit ===================

st.title("Evaluación Inicial de Salud de Mascotas")
st.markdown(
    """
    **Nota:** Esta aplicación utiliza inteligencia artificial para ofrecer una primera opción sobre el estado del animal.  
    La IA puede equivocarse, y ante cualquier duda, es mejor consultar a un veterinario.
    """
)

# Selección del tipo de animal
tipo_animal = st.radio("¿Qué tipo de animal es?", options=["Gato", "Perro"])

# Preguntas generales
comida = st.radio("¿Está comiendo y tomando agua?", options=["Sí", "No"])
eliminacion = st.radio("¿Está orinando y defecando normalmente?", options=["Sí", "No"])
edad = st.number_input("¿Qué edad tiene el animal?", min_value=0, max_value=50, value=3)
acicala = st.radio("¿Se acicala correctamente?", options=["Sí", "No"])

# Preguntas específicas según el tipo de animal
if tipo_animal == "Gato":
    st.subheader("Preguntas adicionales para gatos")
    grooming_regular = st.radio("¿El gato se acicala regularmente?", options=["Sí", "No"])
    cambios_grooming = st.radio("¿Ha habido algún cambio en sus hábitos de acicalamiento?", options=["Sí", "No"])
    comportamiento_cambio = st.radio("¿Ha cambiado recientemente el comportamiento del gato?", options=["Sí", "No"])
    sociable = st.radio("¿El gato es sociable o tímido?", options=["Sociable", "Tímido"])
    ocultarse = st.radio("¿El gato se esconde o evita interactuar?", options=["Sí", "No"])
    reacio = st.radio("¿El gato se muestra reacio a salir incluso para ver a su persona favorita o recibir su comida?", options=["Sí", "No"])
else:
    st.subheader("Preguntas adicionales para perros")
    aseo_regular = st.radio("¿El perro se limpia o se lame regularmente?", options=["Sí", "No"])
    cambios_aseo = st.radio("¿Ha habido algún cambio en sus hábitos de aseo?", options=["Sí", "No"])
    comportamiento_cambio = st.radio("¿Ha cambiado recientemente el comportamiento del perro?", options=["Sí", "No"])
    sociable = st.radio("¿El perro es sociable o muestra timidez/agresividad?", options=["Sociable", "Tímido/Agresivo"])
    ocultarse = st.radio("¿El perro se esconde o evita interactuar?", options=["Sí", "No"])
    reacio = st.radio("¿El perro se muestra reacio a salir incluso para interactuar con su dueño o recibir su comida?", options=["Sí", "No"])

# Opción para subir un video (opcional)
video_file = st.file_uploader("Sube un video del animal (opcional)", type=["mp4", "mov", "avi"])

# Botón para evaluar
if st.button("Evaluar"):
    # Se compila un prompt con la información recopilada
    prompt = f"Evaluación de salud para un {tipo_animal}.\n"
    prompt += f"- Comiendo y bebiendo: {comida}\n"
    prompt += f"- Eliminación normal: {eliminacion}\n"
    prompt += f"- Edad: {edad}\n"
    prompt += f"- Acicalamiento: {acicala}\n\n"
    
    if tipo_animal == "Gato":
        prompt += "Preguntas específicas para gatos:\n"
        prompt += f"- Se acicala regularmente: {grooming_regular}\n"
        prompt += f"- Cambios en el acicalamiento: {cambios_grooming}\n"
        prompt += f"- Cambio en comportamiento: {comportamiento_cambio}\n"
        prompt += f"- Sociabilidad: {sociable}\n"
        prompt += f"- Se esconde: {ocultarse}\n"
        prompt += f"- Reacio a salir: {reacio}\n\n"
    else:
        prompt += "Preguntas específicas para perros:\n"
        prompt += f"- Se limpia o lame regularmente: {aseo_regular}\n"
        prompt += f"- Cambios en hábitos de aseo: {cambios_aseo}\n"
        prompt += f"- Cambio en comportamiento: {comportamiento_cambio}\n"
        prompt += f"- Sociabilidad: {sociable}\n"
        prompt += f"- Se esconde: {ocultarse}\n"
        prompt += f"- Reacio a salir: {reacio}\n\n"
    
    # Agregar criterios de evaluación (se pueden adaptar o ampliar según sea necesario)
    prompt += "Criterios para evaluar la información:\n"
    prompt += "Eyes: Are the eyes half-closed or narrowed? Is there any wrinkling around the eyes?\n"
    prompt += "Nose and Cheeks: Is the bridge of the nose flattened or elongated? Are the cheeks flattened or appear sunken?\n"
    prompt += "Ears: Are the ears turned inward and forward, creating a pointed shape? Has the space between the ears increased?\n"
    prompt += "Whiskers: Are the whiskers stiff and held close to the face? Are the whiskers clumped together? Have the whiskers lost their natural downward curve?\n"
    prompt += "Additional Considerations: Pain Assessment using a validated scale (e.g., Feline Grimace Scale for cats) and species-specific features.\n\n"
    
    if video_file is not None:
        prompt += "Se adjunta un video para análisis visual.\n"
    
    prompt += "\n**Nota:** Esta información es analizada por una IA, la cual puede equivocarse. Ante cualquier duda, consulte a un veterinario."
    
    st.write("El siguiente prompt se enviará a Gemini:")
    st.code(prompt)
    
    # Enviar el prompt a Gemini y mostrar la respuesta
    respuesta = send_prompt_to_gemini(prompt)
    st.subheader("Respuesta de la IA:")
    st.write(respuesta)
